import sqlite3


class CobrancaService:
    def __init__(self, db_path: str, utilizadores):
        self.db_path = db_path
        self.utilizadores = utilizadores

    def init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cobrancas (
                    chave_idempotencia TEXT PRIMARY KEY,
                    viagem_id TEXT NOT NULL,
                    utilizador_id TEXT NOT NULL,
                    valor_centimos INTEGER NOT NULL,
                    meio TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    detalhe TEXT
                )
            """)

    def cobrar(
        self,
        *,
        chave_idempotencia: str,
        viagem_id: str,
        utilizador_id: str,
        valor_centimos: int,
        meio: str,
        mbway_numero: str | None,
    ) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT estado, detalhe FROM cobrancas WHERE chave_idempotencia = ?",
                (chave_idempotencia,),
            ).fetchone()
            if existing:
                return {"estado": existing[0], "detalhe": existing[1]}

            if meio == "CARTAO_ASSOCIADO":
                dados = self.utilizadores.obter_referencia_cartao(utilizador_id)
                aceite = bool(dados)
                detalhe = dados if aceite else "cartão associado inexistente"
            elif meio == "MBWAY":
                aceite = bool(mbway_numero)
                detalhe = mbway_numero if aceite else "número MB WAY em falta"
            else:
                aceite = False
                detalhe = "meio de pagamento inválido"

            estado = "ACEITE" if aceite else "FALHOU"
            conn.execute(
                """INSERT INTO cobrancas
                   (chave_idempotencia, viagem_id, utilizador_id, valor_centimos,
                    meio, estado, detalhe)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    chave_idempotencia,
                    viagem_id,
                    utilizador_id,
                    valor_centimos,
                    meio,
                    estado,
                    detalhe,
                ),
            )
            return {"estado": estado, "detalhe": detalhe}
