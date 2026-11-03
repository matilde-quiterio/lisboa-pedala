from builtins import Exception, print, str
import json
import sqlite3
import contextlib
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, Any

from narwhals import len

from bootstrap import criar_aplicacao
from src.estacoes.comunicacao_docas.service import ResultadoDestrancamento

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
            cursor = conn.execute(
                "SELECT id, payload FROM fila_mensagens WHERE estado = 'PENDENTE'"
            )
            mensagens = cursor.fetchall()

            for msg_id, payload_str in mensagens:
                try:
                    payload = json.loads(payload_str)
                    processador(payload)

                    with conn:
                        conn.execute(
                            "UPDATE fila_mensagens SET estado = 'PROCESSADA' WHERE id = ?",
                            (msg_id,)
                        )
                except Exception as e:
                    print(f"Erro ao processar mensagem {msg_id}: {e}")


def demo_us1():
    print("\n=== US-1 — Desbloquear, devolver e cobrar ===")

    app = criar_aplicacao(
        DB_FILE,
        preco_bloco_centimos=175,
        prazo_retirada_segundos=60,
        timeout_comando_segundos=2,
    )

    app["utilizadores"].adicionar_ficticio(
        "U-001",
        ativo=True,
        tipo_plano="PASSE_ANUAL",
        referencia_cartao="CARD-001",
    )

    app["docas"].registar_doca("D-001", "B-001")
    app["docas"].registar_doca("D-002")

    inicio = datetime.now(timezone.utc)

    print("1. Utilizador identificado: U-001")

    resultado = app["desbloqueio"].desbloquear(
        utilizador_id="U-001",
        bicicleta_id="B-001",
        doca_id="D-001",
        meio_pagamento="MBWAY",
        mbway_numero="910000000",
        resultado_fisico_doca=ResultadoDestrancamento.SUCESSO,
        agora=inicio,
    )

    utilizacao_id = resultado["utilizacao_id"]

    print(f"2. Desbloqueio: {resultado['estado']}")

    viagem = app["viagens"].obter_por_utilizacao(utilizacao_id)
    print(f"   Estado da viagem: {viagem['estado']}")

    retirada = inicio + timedelta(seconds=10)

    app["docas"].retirada_fisica(
        "D-001",
        instante=retirada,
    )

    viagem = app["viagens"].obter_por_utilizacao(utilizacao_id)
    print(f"3. Retirada física: {viagem['estado']}")

    devolucao = retirada + timedelta(minutes=60, seconds=1)

    app["docas"].encaixe_fisico(
        doca_id="D-002",
        bicicleta_id="B-001",
        utilizacao_id=utilizacao_id,
        instante=devolucao,
    )

    viagem = app["viagens"].obter_por_utilizacao(utilizacao_id)

    print(f"4. Devolução física: {viagem['estado']}")
    print(f"5. Tarifa: {viagem['tarifa_centimos'] / 100:.2f} €")
    print(f"6. Cobrança: {viagem['estado_cobranca']}")


def demo_us2():
    repo = ManutencaoRepository(DB_FILE)
    manutencao_svc = ManutencaoService(repo)
    broker = SQLiteBroker(BROKER_DB_FILE)
    telemetria_svc = TelemetriaService(publicar_callback=broker.publicar)

    print("\n=== US-2 — Telemetria e manutenção ===")

    print("1. Bicicleta envia telemetria com avaria...")
    telemetria_svc.receber_telemetria(
        "B-123",
        True,
        "ERR01",
        "Motor sobreaquecido"
    )

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
        print(
            f"   [ID: {ordem.ordem_id[:8]}] "
            f"Bicicleta: {ordem.bicicleta_id} | "
            f"Estado: {ordem.estado.value}"
        )


def main():
    demo_us1()
    demo_us2()


if __name__ == "__main__":
    main()