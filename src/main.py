import json
import sqlite3
import contextlib
from typing import Callable, Dict, Any
from src.manutencao.manutencao import ManutencaoRepository, ManutencaoService
from src.manutencao.telemetria import TelemetriaService

DB_FILE = "lisboa_pedala.db"
BROKER_DB_FILE = "broker.db"

class SQLiteBroker:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS fila_mensagens (
                        id TEXT PRIMARY KEY,
                        payload TEXT NOT NULL,
                        estado TEXT NOT NULL
                    )
                """)

    def publicar(self, mensagem: Dict[str, Any]) -> None:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                conn.execute(
                    "INSERT INTO fila_mensagens (id, payload, estado) VALUES (?, ?, 'PENDENTE') "
                    "ON CONFLICT(id) DO NOTHING",
                    (mensagem["mensagem_id"], json.dumps(mensagem))
                )

    def processar_pendentes(self, processador: Callable[[Dict[str, Any]], None]) -> None:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.execute("SELECT id, payload FROM fila_mensagens WHERE estado = 'PENDENTE'")
            mensagens = cursor.fetchall()
            
            for msg_id, payload_str in mensagens:
                try:
                    payload = json.loads(payload_str)
                    processador(payload)
                    # ACK: Marca como processada se não lançar exceção
                    with conn:
                        conn.execute("UPDATE fila_mensagens SET estado = 'PROCESSADA' WHERE id = ?", (msg_id,))
                except Exception as e:
                    # Falhou: Mantém PENDENTE para nova tentativa futura
                    print(f"Erro ao processar mensagem {msg_id}: {e}")

def main():
    repo = ManutencaoRepository(DB_FILE)
    manutencao_svc = ManutencaoService(repo)
    broker = SQLiteBroker(BROKER_DB_FILE)
    telemetria_svc = TelemetriaService(publicar_callback=broker.publicar)

    print("1. Bicicleta envia telemetria com avaria...")
    telemetria_svc.receber_telemetria("B-123", True, "ERR01", "Motor sobreaquecido")
    
    print("2. Trabalhador do broker processa fila...")
    def consumir(msg: Dict[str, Any]):
        manutencao_svc.processar_avaria_telemetria(
            mensagem_id=msg["mensagem_id"],
            bicicleta_id=msg["bicicleta_id"],
            codigo_avaria=msg["codigo_avaria"],
            descricao=msg["descricao"]
        )
    
    broker.processar_pendentes(consumir)
    
    ordens = manutencao_svc.repo.listar_todas()
    print(f"3. Ordens persistidas na BD: {len(ordens)}")
    for ordem in ordens:
        print(f"   [ID: {ordem.ordem_id[:8]}] Bicicleta: {ordem.bicicleta_id} | Estado: {ordem.estado.value}")

if __name__ == "__main__":
    main()