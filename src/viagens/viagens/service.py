import sqlite3
import uuid
from contextlib import closing


class ConflitoViagemAtiva(Exception):
    pass


class ViagemNaoEncontrada(Exception):
    pass


class ViagensService:
    def __init__(self, db_path: str, tarifacao, cobranca):
        self.db_path = db_path
        self.tarifacao = tarifacao
        self.cobranca = cobranca

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS viagens (
                    id TEXT PRIMARY KEY,
                    utilizacao_id TEXT NOT NULL UNIQUE,
                    utilizador_id TEXT NOT NULL,
                    bicicleta_id TEXT NOT NULL,
                    estado TEXT NOT NULL CHECK (
                        estado IN ('PENDENTE', 'EM_CURSO', 'TERMINADA', 'CANCELADA')
                    ),
                    inicio_fisico TEXT,
                    fim_fisico TEXT,
                    meio_pagamento TEXT NOT NULL,
                    mbway_numero TEXT,
                    tarifa_centimos INTEGER,
                    estado_cobranca TEXT
                );

                CREATE UNIQUE INDEX IF NOT EXISTS uq_viagem_ativa_utilizador
                ON viagens(utilizador_id)
                WHERE estado IN ('PENDENTE', 'EM_CURSO');

                CREATE UNIQUE INDEX IF NOT EXISTS uq_viagem_ativa_bicicleta
                ON viagens(bicicleta_id)
                WHERE estado IN ('PENDENTE', 'EM_CURSO');

                CREATE TABLE IF NOT EXISTS eventos_doca_processados (
                    evento_id TEXT PRIMARY KEY,
                    utilizacao_id TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    instante_fisico TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS devolucoes_antecipadas (
                    utilizacao_id TEXT PRIMARY KEY,
                    evento_id TEXT NOT NULL UNIQUE,
                    bicicleta_id TEXT NOT NULL,
                    doca_id TEXT NOT NULL,
                    instante_fisico TEXT NOT NULL
                );
            """)

    def preparar_viagem(
        self,
        *,
        utilizador_id: str,
        bicicleta_id: str,
        meio_pagamento: str,
        mbway_numero: str | None = None,
    ) -> dict:
        viagem_id = str(uuid.uuid4())
        utilizacao_id = str(uuid.uuid4())
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conflito = conn.execute(
                """SELECT 1 FROM viagens
                   WHERE estado IN ('PENDENTE','EM_CURSO')
                     AND (utilizador_id = ? OR bicicleta_id = ?)
                   LIMIT 1""",
                (utilizador_id, bicicleta_id),
            ).fetchone()
            if conflito:
                raise ConflitoViagemAtiva(
                    "utilizador ou bicicleta já possui viagem PENDENTE/EM_CURSO"
                )
            conn.execute(
                """INSERT INTO viagens
                   (id, utilizacao_id, utilizador_id, bicicleta_id, estado,
                    meio_pagamento, mbway_numero)
                   VALUES (?, ?, ?, ?, 'PENDENTE', ?, ?)""",
                (
                    viagem_id,
                    utilizacao_id,
                    utilizador_id,
                    bicicleta_id,
                    meio_pagamento,
                    mbway_numero,
                ),
            )
            conn.commit()
            return {"viagem_id": viagem_id, "utilizacao_id": utilizacao_id}
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            raise ConflitoViagemAtiva(
                "utilizador ou bicicleta já possui viagem PENDENTE/EM_CURSO"
            ) from exc
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def cancelar_pendente(self, utilizacao_id: str) -> bool:
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(
                """UPDATE viagens SET estado = 'CANCELADA'
                   WHERE utilizacao_id = ? AND estado = 'PENDENTE'""",
                (utilizacao_id,),
            )
            return cur.rowcount == 1

    def processar_evento_doca(
        self,
        *,
        evento_id: str,
        utilizacao_id: str,
        tipo: str,
        bicicleta_id: str,
        doca_id: str,
        instante_fisico: str,
    ) -> dict:
        """Regista idempotentemente o evento e atualiza a viagem na mesma transação."""
        conn = self._connect()
        fechou = False
        try:
            conn.execute("BEGIN IMMEDIATE")
            ja = conn.execute(
                "SELECT 1 FROM eventos_doca_processados WHERE evento_id = ?",
                (evento_id,),
            ).fetchone()
            if ja:
                conn.rollback()
                return {"duplicado": True, "fechou": False}

            viagem = conn.execute(
                "SELECT * FROM viagens WHERE utilizacao_id = ?",
                (utilizacao_id,),
            ).fetchone()
            if not viagem:
                raise ViagemNaoEncontrada(utilizacao_id)
            if viagem["bicicleta_id"] != bicicleta_id:
                raise ValueError("evento não corresponde à bicicleta da utilização")

            if tipo == "RETIRADA":
                if viagem["estado"] == "PENDENTE" and viagem["inicio_fisico"] is None:
                    conn.execute(
                        """UPDATE viagens
                           SET estado = 'EM_CURSO', inicio_fisico = ?
                           WHERE utilizacao_id = ?""",
                        (instante_fisico, utilizacao_id),
                    )
                    pendente = conn.execute(
                        "SELECT instante_fisico FROM devolucoes_antecipadas WHERE utilizacao_id = ?",
                        (utilizacao_id,),
                    ).fetchone()
                    if pendente:
                        conn.execute(
                            """UPDATE viagens SET estado = 'TERMINADA', fim_fisico = ?
                               WHERE utilizacao_id = ?""",
                            (pendente[0], utilizacao_id),
                        )
                        conn.execute(
                            "DELETE FROM devolucoes_antecipadas WHERE utilizacao_id = ?",
                            (utilizacao_id,),
                        )
                        fechou = True
                # Se já começou/terminou, não substituir o instante físico confirmado.

            elif tipo == "ENCAIXE":
                if viagem["estado"] == "EM_CURSO":
                    if viagem["fim_fisico"] is None:
                        conn.execute(
                            """UPDATE viagens SET estado = 'TERMINADA', fim_fisico = ?
                               WHERE utilizacao_id = ?""",
                            (instante_fisico, utilizacao_id),
                        )
                        fechou = True
                elif viagem["estado"] == "PENDENTE":
                    conn.execute(
                        """INSERT OR IGNORE INTO devolucoes_antecipadas
                           (utilizacao_id, evento_id, bicicleta_id, doca_id, instante_fisico)
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            utilizacao_id,
                            evento_id,
                            bicicleta_id,
                            doca_id,
                            instante_fisico,
                        ),
                    )
            elif tipo == "REBLOQUEIO_SEM_RETIRADA":
                if viagem["estado"] == "PENDENTE" and viagem["inicio_fisico"] is None:
                    conn.execute(
                        "UPDATE viagens SET estado = 'CANCELADA' WHERE utilizacao_id = ?",
                        (utilizacao_id,),
                    )
            else:
                raise ValueError(f"tipo de evento desconhecido: {tipo}")

            conn.execute(
                """INSERT INTO eventos_doca_processados
                   (evento_id, utilizacao_id, tipo, instante_fisico)
                   VALUES (?, ?, ?, ?)""",
                (evento_id, utilizacao_id, tipo, instante_fisico),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        if fechou:
            self._tarifar_e_cobrar(utilizacao_id)
        return {"duplicado": False, "fechou": fechou}

    def _tarifar_e_cobrar(self, utilizacao_id: str) -> None:
        with closing(self._connect()) as conn, conn:
            viagem = conn.execute(
                "SELECT * FROM viagens WHERE utilizacao_id = ?", (utilizacao_id,)
            ).fetchone()
        if not viagem or viagem["estado"] != "TERMINADA":
            return

        # Idempotência da coordenação: se a tarifa já foi persistida, não recalcular.
        valor = viagem["tarifa_centimos"]
        if valor is None:
            valor = self.tarifacao.calcular(
                viagem["utilizador_id"],
                viagem["inicio_fisico"],
                viagem["fim_fisico"],
            )
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    """UPDATE viagens SET tarifa_centimos = ?
                       WHERE utilizacao_id = ? AND tarifa_centimos IS NULL""",
                    (valor, utilizacao_id),
                )

        if valor == 0:
            return

        resultado = self.cobranca.cobrar(
            chave_idempotencia=f"cobranca:{viagem['id']}",
            viagem_id=viagem["id"],
            utilizador_id=viagem["utilizador_id"],
            valor_centimos=valor,
            meio=viagem["meio_pagamento"],
            mbway_numero=viagem["mbway_numero"],
        )
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE viagens SET estado_cobranca = ? WHERE utilizacao_id = ?",
                (resultado["estado"], utilizacao_id),
            )

    def reprocessar_conclusao(self, utilizacao_id: str) -> dict:
        """
        Repete tarifação/cobrança de uma viagem já TERMINADA
        sem reprocessar o evento físico de devolução.
        """
        viagem = self.obter_por_utilizacao(utilizacao_id)

        if not viagem:
            raise ViagemNaoEncontrada(utilizacao_id)

        if viagem["estado"] != "TERMINADA":
            raise ValueError(
                "só é possível reprocessar uma viagem TERMINADA"
            )

        self._tarifar_e_cobrar(utilizacao_id)

        return self.obter_por_utilizacao(utilizacao_id)

    def obter_por_utilizacao(self, utilizacao_id: str) -> dict | None:
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT * FROM viagens WHERE utilizacao_id = ?", (utilizacao_id,)
            ).fetchone()
        return dict(row) if row else None