from datetime import datetime, timedelta, timezone
from contextlib import closing
import sqlite3
import uuid


class PoliticaRetencaoNaoDefinida(RuntimeError):
    pass


class ResultadoDestrancamento:
    SUCESSO = "SUCESSO"
    FALHA = "FALHA"
    TIMEOUT = "TIMEOUT"


class ComunicacaoDocasService:
    """Simulação concreta da doca, incluindo prazo local e buffer de 24 h."""

    RETENCAO_EVENTOS = timedelta(hours=24)

    def __init__(self, db_path: str, viagens, *, prazo_retirada_segundos: int, timeout_comando_segundos: float):
        if prazo_retirada_segundos <= 0:
            raise ValueError("prazo_retirada_segundos tem de ser > 0")
        self.db_path = db_path
        self.viagens = viagens
        if timeout_comando_segundos <= 0:
            raise ValueError("timeout_comando_segundos tem de ser > 0")
        self.prazo_retirada_segundos = prazo_retirada_segundos
        self.timeout_comando_segundos = timeout_comando_segundos

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS estado_docas_simuladas (
                    doca_id TEXT PRIMARY KEY,
                    online INTEGER NOT NULL DEFAULT 1,
                    bicicleta_id TEXT,
                    utilizacao_id TEXT,
                    destrancada INTEGER NOT NULL DEFAULT 0,
                    retirada INTEGER NOT NULL DEFAULT 0,
                    deadline_retirada TEXT
                );

                CREATE TABLE IF NOT EXISTS buffer_eventos_doca (
                    evento_id TEXT PRIMARY KEY,
                    utilizacao_id TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    bicicleta_id TEXT NOT NULL,
                    doca_id TEXT NOT NULL,
                    instante_fisico TEXT NOT NULL,
                    guardado_em TEXT NOT NULL
                );
            """)

    def registar_doca(self, doca_id: str, bicicleta_id: str | None = None) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """INSERT OR REPLACE INTO estado_docas_simuladas
                   (doca_id, online, bicicleta_id, utilizacao_id, destrancada, retirada, deadline_retirada)
                   VALUES (?, 1, ?, NULL, 0, 0, NULL)""",
                (doca_id, bicicleta_id),
            )

    def definir_online(self, doca_id: str, online: bool, *, agora: datetime | None = None) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE estado_docas_simuladas SET online = ? WHERE doca_id = ?",
                (int(online), doca_id),
            )
        if online:
            self.reenviar_eventos(doca_id, agora=agora)

    def destrancar(
        self,
        *,
        doca_id: str,
        bicicleta_id: str,
        utilizacao_id: str,
        resultado_fisico: str,
        atraso_resposta_segundos: float = 0,
        agora: datetime | None = None,
    ) -> str:
        agora = agora or datetime.now(timezone.utc)
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT * FROM estado_docas_simuladas WHERE doca_id = ?", (doca_id,)
            ).fetchone()
            if not row or not row["online"]:
                return ResultadoDestrancamento.TIMEOUT

            if resultado_fisico not in (ResultadoDestrancamento.SUCESSO, ResultadoDestrancamento.FALHA):
                raise ValueError("resultado_fisico inválido")

            # A doca executa fisicamente a operação; o backend pode deixar de receber
            # a resposta se ela ultrapassar o timeout configurado.
            if resultado_fisico == ResultadoDestrancamento.SUCESSO:
                deadline = agora + timedelta(seconds=self.prazo_retirada_segundos)
                conn.execute(
                """UPDATE estado_docas_simuladas
                   SET bicicleta_id = ?, utilizacao_id = ?, destrancada = 1,
                       retirada = 0, deadline_retirada = ?
                   WHERE doca_id = ?""",
                    (bicicleta_id, utilizacao_id, deadline.isoformat(), doca_id),
                )

        if atraso_resposta_segundos > self.timeout_comando_segundos:
            return ResultadoDestrancamento.TIMEOUT
        return resultado_fisico

    def retirada_fisica(
        self, doca_id: str, *, instante: datetime | None = None
    ) -> str:
        instante = instante or datetime.now(timezone.utc)
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT * FROM estado_docas_simuladas WHERE doca_id = ?", (doca_id,)
            ).fetchone()
            if not row or not row["utilizacao_id"]:
                raise ValueError("doca sem utilização preparada/destrancada")
            conn.execute(
                """UPDATE estado_docas_simuladas
                   SET retirada = 1, destrancada = 0, deadline_retirada = NULL
                   WHERE doca_id = ?""",
                (doca_id,),
            )
            evento = self._novo_evento(row, "RETIRADA", instante)
        self._entregar_ou_guardar(evento)
        return evento["evento_id"]

    def encaixe_fisico(
        self,
        *,
        doca_id: str,
        bicicleta_id: str,
        utilizacao_id: str,
        instante: datetime | None = None,
    ) -> str:
        instante = instante or datetime.now(timezone.utc)
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT * FROM estado_docas_simuladas WHERE doca_id = ?", (doca_id,)
            ).fetchone()
            if not row:
                raise ValueError("doca inexistente")
            evento = {
                "evento_id": str(uuid.uuid4()),
                "utilizacao_id": utilizacao_id,
                "tipo": "ENCAIXE",
                "bicicleta_id": bicicleta_id,
                "doca_id": doca_id,
                "instante_fisico": instante.isoformat(),
            }
            conn.execute(
                """UPDATE estado_docas_simuladas
                   SET bicicleta_id = ?, utilizacao_id = NULL, destrancada = 0,
                       retirada = 0, deadline_retirada = NULL
                   WHERE doca_id = ?""",
                (bicicleta_id, doca_id),
            )
        self._entregar_ou_guardar(evento)
        return evento["evento_id"]

    def processar_prazos(self, *, agora: datetime | None = None) -> int:
        """Relógio local da simulação: rebloqueia deadlines expirados mesmo offline."""
        agora = agora or datetime.now(timezone.utc)
        eventos = []
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                """SELECT * FROM estado_docas_simuladas
                   WHERE destrancada = 1 AND retirada = 0 AND deadline_retirada IS NOT NULL"""
            ).fetchall()
            for row in rows:
                deadline = datetime.fromisoformat(row["deadline_retirada"])
                if agora >= deadline:
                    evento = self._novo_evento(row, "REBLOQUEIO_SEM_RETIRADA", agora)
                    eventos.append(evento)
                    conn.execute(
                        """UPDATE estado_docas_simuladas
                           SET destrancada = 0, utilizacao_id = NULL, deadline_retirada = NULL
                           WHERE doca_id = ?""",
                        (row["doca_id"],),
                    )
        for evento in eventos:
            self._entregar_ou_guardar(evento, guardado_em=agora)
        return len(eventos)

    def reenviar_eventos(self, doca_id: str, *, agora: datetime | None = None) -> int:
        agora = agora or datetime.now(timezone.utc)
        cutoff = (agora - self.RETENCAO_EVENTOS).isoformat()
        enviados = 0
        with closing(self._connect()) as conn, conn:
            expirado = conn.execute(
                """SELECT evento_id FROM buffer_eventos_doca
                   WHERE doca_id = ? AND guardado_em < ? LIMIT 1""",
                (doca_id, cutoff),
            ).fetchone()
            if expirado:
                raise PoliticaRetencaoNaoDefinida(
                    "Existe evento local com mais de 24h. Os ADRs definem o limite "
                    "de armazenamento, mas não definem a política após esse limite."
                )
            rows = conn.execute(
                """SELECT * FROM buffer_eventos_doca
                   WHERE doca_id = ? ORDER BY guardado_em, rowid""",
                (doca_id,),
            ).fetchall()
        for row in rows:
            try:
                self._encaminhar(dict(row))
            except Exception:
                break
            else:
                with closing(self._connect()) as conn, conn:
                    conn.execute(
                        "DELETE FROM buffer_eventos_doca WHERE evento_id = ?",
                        (row["evento_id"],),
                    )
                enviados += 1
        return enviados

    def reenviar_evento_duplicado(self, evento_id: str) -> None:
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT * FROM buffer_eventos_doca WHERE evento_id = ?", (evento_id,)
            ).fetchone()
        if row:
            self._encaminhar(dict(row))

    def _novo_evento(self, row, tipo: str, instante: datetime) -> dict:
        return {
            "evento_id": str(uuid.uuid4()),
            "utilizacao_id": row["utilizacao_id"],
            "tipo": tipo,
            "bicicleta_id": row["bicicleta_id"],
            "doca_id": row["doca_id"],
            "instante_fisico": instante.isoformat(),
        }

    def _entregar_ou_guardar(self, evento: dict, guardado_em: datetime | None = None) -> None:
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT online FROM estado_docas_simuladas WHERE doca_id = ?",
                (evento["doca_id"],),
            ).fetchone()
        if row and row[0]:
            try:
                self._encaminhar(evento)
                return
            except Exception:
                pass
        self._guardar(evento, guardado_em or datetime.now(timezone.utc))

    def _guardar(self, evento: dict, guardado_em: datetime) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """INSERT OR IGNORE INTO buffer_eventos_doca
                   (evento_id, utilizacao_id, tipo, bicicleta_id, doca_id,
                    instante_fisico, guardado_em)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    evento["evento_id"], evento["utilizacao_id"], evento["tipo"],
                    evento["bicicleta_id"], evento["doca_id"],
                    evento["instante_fisico"], guardado_em.isoformat(),
                ),
            )

    def _encaminhar(self, evento: dict) -> None:
        self.viagens.processar_evento_doca(
            evento_id=evento["evento_id"],
            utilizacao_id=evento["utilizacao_id"],
            tipo=evento["tipo"],
            bicicleta_id=evento["bicicleta_id"],
            doca_id=evento["doca_id"],
            instante_fisico=evento["instante_fisico"],
        )