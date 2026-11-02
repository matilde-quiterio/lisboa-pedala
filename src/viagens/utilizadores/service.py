import sqlite3


class UtilizadoresService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS utilizadores (
                    id TEXT PRIMARY KEY,
                    ativo INTEGER NOT NULL CHECK (ativo IN (0, 1)),
                    tipo_plano TEXT NOT NULL,
                    referencia_cartao TEXT
                )
            """)

    def adicionar_ficticio(
        self,
        utilizador_id: str,
        *,
        ativo: bool,
        tipo_plano: str,
        referencia_cartao: str | None = None,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO utilizadores
                   (id, ativo, tipo_plano, referencia_cartao)
                   VALUES (?, ?, ?, ?)""",
                (utilizador_id, int(ativo), tipo_plano, referencia_cartao),
            )

    def validar(self, utilizador_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT ativo FROM utilizadores WHERE id = ?", (utilizador_id,)
            ).fetchone()
        return bool(row and row[0] == 1)

    def obter_tipo_plano(self, utilizador_id: str) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT tipo_plano FROM utilizadores WHERE id = ?", (utilizador_id,)
            ).fetchone()
        return row[0] if row else None

    def obter_referencia_cartao(self, utilizador_id: str) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT referencia_cartao FROM utilizadores WHERE id = ?",
                (utilizador_id,),
            ).fetchone()
        return row[0] if row else None
