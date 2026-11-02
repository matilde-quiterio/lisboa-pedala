import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal

from .modelos import EstadoViagem, Viagem


class RepositorioViagensSQLite:

    def __init__(self, caminho_bd: str):
        self.caminho_bd = caminho_bd
        self._criar_tabelas()

    def _ligar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.caminho_bd)
        conn.row_factory = sqlite3.Row
        return conn

    def _criar_tabelas(self) -> None:
        with self._ligar() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS viagens (
                    id TEXT PRIMARY KEY,
                    utilizador_id TEXT NOT NULL,
                    bicicleta_id TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    criada_em TEXT NOT NULL,

                    inicio TEXT,
                    fim TEXT,

                    estacao_inicio_id TEXT,
                    estacao_fim_id TEXT,

                    metodo_pagamento TEXT,
                    dados_pagamento TEXT,

                    tarifa TEXT,
                    cobranca_concluida INTEGER NOT NULL DEFAULT 0,

                    evento_retirada_id TEXT,
                    evento_devolucao_id TEXT,

                    devolucao_pendente_em TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS eventos_processados (
                    evento_id TEXT PRIMARY KEY,
                    viagem_id TEXT NOT NULL
                )
                """
            )

    @contextmanager
    def transacao(self):
        conn = self._ligar()

        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    def guardar(
        self,
        conn: sqlite3.Connection,
        viagem: Viagem,
    ) -> None:

        conn.execute(
            """
            INSERT INTO viagens (
                id,
                utilizador_id,
                bicicleta_id,
                estado,
                criada_em,
                inicio,
                fim,
                estacao_inicio_id,
                estacao_fim_id,
                metodo_pagamento,
                dados_pagamento,
                tarifa,
                cobranca_concluida,
                evento_retirada_id,
                evento_devolucao_id,
                devolucao_pendente_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(id) DO UPDATE SET
                estado = excluded.estado,
                inicio = excluded.inicio,
                fim = excluded.fim,
                estacao_inicio_id = excluded.estacao_inicio_id,
                estacao_fim_id = excluded.estacao_fim_id,
                metodo_pagamento = excluded.metodo_pagamento,
                dados_pagamento = excluded.dados_pagamento,
                tarifa = excluded.tarifa,
                cobranca_concluida = excluded.cobranca_concluida,
                evento_retirada_id = excluded.evento_retirada_id,
                evento_devolucao_id = excluded.evento_devolucao_id,
                devolucao_pendente_em = excluded.devolucao_pendente_em
            """,
            (
                viagem.id,
                viagem.utilizador_id,
                viagem.bicicleta_id,
                viagem.estado.value,
                viagem.criada_em.isoformat(),
                viagem.inicio.isoformat() if viagem.inicio else None,
                viagem.fim.isoformat() if viagem.fim else None,
                viagem.estacao_inicio_id,
                viagem.estacao_fim_id,
                viagem.metodo_pagamento,
                json.dumps(viagem.dados_pagamento)
                if viagem.dados_pagamento is not None
                else None,
                str(viagem.tarifa)
                if viagem.tarifa is not None
                else None,
                int(viagem.cobranca_concluida),
                viagem.evento_retirada_id,
                viagem.evento_devolucao_id,
                viagem.devolucao_pendente_em.isoformat()
                if viagem.devolucao_pendente_em
                else None,
            ),
        )

    def obter_por_id(
        self,
        conn: sqlite3.Connection,
        viagem_id: str,
    ) -> Viagem | None:

        row = conn.execute(
            """
            SELECT *
            FROM viagens
            WHERE id = ?
            """,
            (viagem_id,),
        ).fetchone()

        return self._converter(row)

    def obter_aberta_por_bicicleta(
        self,
        conn: sqlite3.Connection,
        bicicleta_id: str,
    ) -> Viagem | None:

        row = conn.execute(
            """
            SELECT *
            FROM viagens
            WHERE bicicleta_id = ?
              AND estado IN ('PENDENTE', 'EM_CURSO')
            ORDER BY criada_em DESC
            LIMIT 1
            """,
            (bicicleta_id,),
        ).fetchone()

        return self._converter(row)

    def existe_viagem_ativa_utilizador(
        self,
        conn: sqlite3.Connection,
        utilizador_id: str,
    ) -> bool:

        row = conn.execute(
            """
            SELECT 1
            FROM viagens
            WHERE utilizador_id = ?
              AND estado IN ('PENDENTE', 'EM_CURSO')
            LIMIT 1
            """,
            (utilizador_id,),
        ).fetchone()

        return row is not None

    def existe_viagem_ativa_bicicleta(
        self,
        conn: sqlite3.Connection,
        bicicleta_id: str,
    ) -> bool:

        row = conn.execute(
            """
            SELECT 1
            FROM viagens
            WHERE bicicleta_id = ?
              AND estado IN ('PENDENTE', 'EM_CURSO')
            LIMIT 1
            """,
            (bicicleta_id,),
        ).fetchone()

        return row is not None

    def evento_ja_processado(
        self,
        conn: sqlite3.Connection,
        evento_id: str,
    ) -> bool:

        row = conn.execute(
            """
            SELECT 1
            FROM eventos_processados
            WHERE evento_id = ?
            """,
            (evento_id,),
        ).fetchone()

        return row is not None

    def marcar_evento_processado(
        self,
        conn: sqlite3.Connection,
        evento_id: str,
        viagem_id: str,
    ) -> None:

        conn.execute(
            """
            INSERT INTO eventos_processados (
                evento_id,
                viagem_id
            )
            VALUES (?, ?)
            """,
            (evento_id, viagem_id),
        )

    def obter_por_id_fora_transacao(
        self,
        viagem_id: str,
    ) -> Viagem | None:

        with self._ligar() as conn:
            return self.obter_por_id(conn, viagem_id)

    def _converter(self, row) -> Viagem | None:

        if row is None:
            return None

        return Viagem(
            id=row["id"],
            utilizador_id=row["utilizador_id"],
            bicicleta_id=row["bicicleta_id"],
            estado=EstadoViagem(row["estado"]),
            criada_em=datetime.fromisoformat(row["criada_em"]),
            inicio=(
                datetime.fromisoformat(row["inicio"])
                if row["inicio"]
                else None
            ),
            fim=(
                datetime.fromisoformat(row["fim"])
                if row["fim"]
                else None
            ),
            estacao_inicio_id=row["estacao_inicio_id"],
            estacao_fim_id=row["estacao_fim_id"],
            metodo_pagamento=row["metodo_pagamento"],
            dados_pagamento=(
                json.loads(row["dados_pagamento"])
                if row["dados_pagamento"]
                else None
            ),
            tarifa=(
                Decimal(row["tarifa"])
                if row["tarifa"] is not None
                else None
            ),
            cobranca_concluida=bool(
                row["cobranca_concluida"]
            ),
            evento_retirada_id=row["evento_retirada_id"],
            evento_devolucao_id=row["evento_devolucao_id"],
            devolucao_pendente_em=(
                datetime.fromisoformat(
                    row["devolucao_pendente_em"]
                )
                if row["devolucao_pendente_em"]
                else None
            ),
        )