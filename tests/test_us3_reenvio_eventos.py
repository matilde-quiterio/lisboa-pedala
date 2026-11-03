import os
import sqlite3
import pytest
from datetime import datetime, timedelta, timezone

from src.estacoes.comunicacao_docas.service import ComunicacaoDocasService, ResultadoDestrancamento
from src.viagens.viagens.service import ViagensService

DB_DOCAS = "test_docas.db"
DB_VIAGENS = "test_viagens.db"

class MockTarifacao:
    def calcular(self, utilizador_id, inicio, fim):
        return 150  # 1.50 euros

class MockCobranca:
    def __init__(self):
        self.cobrancas = []

    def cobrar(self, chave_idempotencia, viagem_id, utilizador_id, valor_centimos, meio, mbway_numero):
        # Regista todas as chamadas recebidas para que o teste valide a 
        # idempotência da coordenação feita pelo ViagensService.
        self.cobrancas.append({
            "chave_idempotencia": chave_idempotencia,
            "valor": valor_centimos
        })
        return {"estado": "SUCESSO"}


@pytest.fixture(autouse=True)
def setup_teardown():
    for db in [DB_DOCAS, DB_VIAGENS]:
        if os.path.exists(db):
            os.remove(db)
            
    yield
    
    for db in [DB_DOCAS, DB_VIAGENS]:
        if os.path.exists(db):
            os.remove(db)


def test_us3_evento_offline_guardado_e_reenviado_atualiza_instante_fisico_sem_duplicar():
    """
    Verifica que:
    1. Um evento ocorrido enquanto a doca está sem rede fica guardado.
    2. O reenvio usa o instante físico original.
    3. Reenvio duplicado do mesmo evento não duplica viagem nem a cobrança.
    """
    mock_tarifacao = MockTarifacao()
    mock_cobranca = MockCobranca()
    
    viagens_svc = ViagensService(DB_VIAGENS, mock_tarifacao, mock_cobranca)
    viagens_svc.init_schema()

    docas_svc = ComunicacaoDocasService(DB_DOCAS, viagens_svc, prazo_retirada_segundos=30, timeout_comando_segundos=2.0)
    docas_svc.init_schema()

    doca_id = "DOCA-01"
    bicicleta_id = "BIKE-01"
    utilizador_id = "USER-1"
    
    docas_svc.registar_doca(doca_id, bicicleta_id)

    # 1. Preparar e iniciar a viagem normalmente online
    prep = viagens_svc.preparar_viagem(
        utilizador_id=utilizador_id, 
        bicicleta_id=bicicleta_id, 
        meio_pagamento="MBWAY", 
        mbway_numero="912345678"
    )
    utilizacao_id = prep["utilizacao_id"]
    
    # Destrancar a doca
    docas_svc.destrancar(doca_id=doca_id, bicicleta_id=bicicleta_id, utilizacao_id=utilizacao_id, resultado_fisico=ResultadoDestrancamento.SUCESSO)
    
    # Retirada física online
    instante_retirada = datetime.now(timezone.utc) - timedelta(minutes=50)
    docas_svc.retirada_fisica(doca_id, instante=instante_retirada)
    
    # 2. Doca perde a ligação à rede
    docas_svc.definir_online(doca_id, False)

    # 3. Doca recebe o encaixe físico (offline)
    instante_encaixe = datetime.now(timezone.utc)
    evento_id_encaixe = docas_svc.encaixe_fisico(
        doca_id=doca_id, 
        bicicleta_id=bicicleta_id, 
        utilizacao_id=utilizacao_id, 
        instante=instante_encaixe
    )
    
    # Verifica que a viagem continua EM_CURSO no backend e não foi fechada nem cobrada
    viagem_backend = viagens_svc.obter_por_utilizacao(utilizacao_id)
    assert viagem_backend["estado"] == "EM_CURSO"
    assert len(mock_cobranca.cobrancas) == 0

    # 4. Restabelece a rede. Isto deve reenviar o evento automaticamente através do Comunicação das Docas
    docas_svc.definir_online(doca_id, True, agora=instante_encaixe + timedelta(minutes=5))

    # Verifica se a viagem fechou com os instantes físicos corretos e originou cobrança
    viagem_atualizada = viagens_svc.obter_por_utilizacao(utilizacao_id)
    assert viagem_atualizada["estado"] == "TERMINADA"
    assert viagem_atualizada["inicio_fisico"] == instante_retirada.isoformat()
    assert viagem_atualizada["fim_fisico"] == instante_encaixe.isoformat()
    
    assert len(mock_cobranca.cobrancas) == 1
    assert mock_cobranca.cobrancas[0]["valor"] == 150

    # 5. Força reenvio do MESMO evento entregando-o diretamente a Viagens
    resultado = viagens_svc.processar_evento_doca(
        evento_id=evento_id_encaixe,
        utilizacao_id=utilizacao_id,
        tipo="ENCAIXE",
        bicicleta_id=bicicleta_id,
        doca_id=doca_id,
        instante_fisico=instante_encaixe.isoformat()
    )
    
    # Valida que o processamento deteta o duplicado e não avança
    assert resultado["duplicado"] is True
    assert resultado["fechou"] is False
    
    # Confirma que a cobrança NÃO foi chamada segunda vez
    assert len(mock_cobranca.cobrancas) == 1