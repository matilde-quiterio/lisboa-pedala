import contextlib
import os
import sqlite3

import pytest

from src.main import SQLiteBroker
from src.manutencao.manutencao import (
    EstadoOrdem,
    ManutencaoRepository,
    ManutencaoService,
)
from src.manutencao.telemetria import TelemetriaService


TEST_DB = "test_manutencao.db"
TEST_BROKER_DB = "test_broker.db"
MIGRACAO_DB = "test_migracao.db"


@pytest.fixture(autouse=True)
def setup_teardown():
    bases_de_dados = [TEST_DB, TEST_BROKER_DB, MIGRACAO_DB]

    for db in bases_de_dados:
        if os.path.exists(db):
            os.remove(db)

    yield

    for db in bases_de_dados:
        if os.path.exists(db):
            os.remove(db)


def test_ciclo_vida_sem_intervencao():
    repo = ManutencaoRepository(TEST_DB)
    manutencao = ManutencaoService(repo)
    ordem = manutencao.reportar_avaria_manual("BIKE-1", "Avaria leve")

    fechada = manutencao.avaliar_ordem(
        ordem_id=ordem.ordem_id,
        necessita_intervencao=False,
        resultado="Falso alarme, verificado visualmente",
    )

    assert fechada.estado == EstadoOrdem.SEM_INTERVENCAO_NECESSARIA
    assert fechada.necessita_intervencao is False
    assert fechada.resultado == "Falso alarme, verificado visualmente"


def test_ciclo_vida_com_intervencao_e_persistencia():
    repo1 = ManutencaoRepository(TEST_DB)
    manutencao1 = ManutencaoService(repo1)
    ordem = manutencao1.reportar_avaria_manual("BIKE-2", "Avaria motor")

    em_intervencao = manutencao1.avaliar_ordem(
        ordem_id=ordem.ordem_id,
        necessita_intervencao=True,
    )
    assert em_intervencao.estado == EstadoOrdem.EM_INTERVENCAO

    repo2 = ManutencaoRepository(TEST_DB)
    manutencao2 = ManutencaoService(repo2)
    ordem_recuperada = repo2.obter_por_id(ordem.ordem_id)

    assert ordem_recuperada is not None
    assert ordem_recuperada.estado == EstadoOrdem.EM_INTERVENCAO

    concluida = manutencao2.registar_intervencao(
        ordem_id=ordem.ordem_id,
        descricao_intervencao="Substituição do motor elétrico",
        resultado="Sistema testado e operacional",
    )

    assert concluida.estado == EstadoOrdem.CONCLUIDA
    assert concluida.descricao_intervencao == "Substituição do motor elétrico"
    assert concluida.resultado == "Sistema testado e operacional"


def test_transicoes_invalidas_rejeitadas():
    repo = ManutencaoRepository(TEST_DB)
    manutencao = ManutencaoService(repo)
    ordem = manutencao.reportar_avaria_manual("BIKE-3", "Falha de ecrã")

    with pytest.raises(ValueError, match="não se encontra em intervenção"):
        manutencao.registar_intervencao(
            ordem.ordem_id, "Troca de ecrã", "OK"
        )

    manutencao.avaliar_ordem(
        ordem.ordem_id,
        necessita_intervencao=False,
        resultado="Ecrã apenas sujo",
    )

    with pytest.raises(
        ValueError,
        match="Não é possível avaliar a ordem a partir do estado",
    ):
        manutencao.avaliar_ordem(
            ordem.ordem_id,
            necessita_intervencao=True,
        )


def test_migracao_estado_cancelada_preserva_dados():
    with contextlib.closing(sqlite3.connect(MIGRACAO_DB)) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE ordens_manutencao (
                    ordem_id TEXT PRIMARY KEY,
                    bicicleta_id TEXT NOT NULL,
                    origem TEXT NOT NULL,
                    descricao_avaria TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    mensagem_id_origem TEXT UNIQUE,
                    resultado TEXT
                )
            """)
            conn.execute("""
                INSERT INTO ordens_manutencao (
                    ordem_id, bicicleta_id, origem, descricao_avaria,
                    estado, mensagem_id_origem, resultado
                ) VALUES (
                    'ORD-ANTIGA', 'BIKE-MIG', 'MANUAL',
                    'Avaria Antiga', 'CANCELADA', NULL, 'Fechado sem ação'
                )
            """)

    repo = ManutencaoRepository(MIGRACAO_DB)
    ordem_migrada = repo.obter_por_id("ORD-ANTIGA")

    assert ordem_migrada is not None
    assert ordem_migrada.bicicleta_id == "BIKE-MIG"
    assert ordem_migrada.resultado == "Fechado sem ação"
    assert ordem_migrada.estado == EstadoOrdem.SEM_INTERVENCAO_NECESSARIA
    assert ordem_migrada.necessita_intervencao is False


def test_erro_explicito_para_estados_desconhecidos():
    repo = ManutencaoRepository(MIGRACAO_DB)

    with contextlib.closing(sqlite3.connect(MIGRACAO_DB)) as conn:
        with conn:
            conn.execute("""
                INSERT INTO ordens_manutencao (
                    ordem_id, bicicleta_id, origem, descricao_avaria,
                    estado, mensagem_id_origem, resultado
                ) VALUES (
                    'ORD-ERR', 'B1', 'MANUAL', 'Desc',
                    'ESTADO_INVENTADO_NOVO', NULL, NULL
                )
            """)

    with pytest.raises(
        ValueError,
        match="Estado desconhecido ou corrompido na base de dados: "
              "'ESTADO_INVENTADO_NOVO'",
    ):
        repo.obter_por_id("ORD-ERR")


def test_mensagem_pendente_sobrevive_a_reabertura_do_broker():
    broker1 = SQLiteBroker(TEST_BROKER_DB)
    telemetria = TelemetriaService(publicar_callback=broker1.publicar)
    telemetria.receber_telemetria("BIKE-5", True, "ERR", "Avaria")

    def falhar(_mensagem):
        raise RuntimeError("Falha temporária")

    broker1.processar_pendentes(falhar)

    broker2 = SQLiteBroker(TEST_BROKER_DB)
    repo = ManutencaoRepository(TEST_DB)
    manutencao = ManutencaoService(repo)

    broker2.processar_pendentes(
        lambda msg: manutencao.processar_avaria_telemetria(
            msg["mensagem_id"],
            msg["bicicleta_id"],
            msg["codigo_avaria"],
            msg["descricao"],
        )
    )

    assert len(repo.listar_todas()) == 1