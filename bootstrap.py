from src.viagens.utilizadores.service import UtilizadoresService
from src.viagens.tarifacao.service import TarifacaoService
from src.viagens.cobranca.service import CobrancaService
from src.viagens.viagens.service import ViagensService
from src.estacoes.comunicacao_docas.service import ComunicacaoDocasService
from src.viagens.desbloqueio.service import DesbloqueioService


def criar_aplicacao(
    db_path: str,
    *,
    preco_bloco_centimos: int,
    prazo_retirada_segundos: int,
    timeout_comando_segundos: float,
):
    utilizadores = UtilizadoresService(db_path)
    tarifacao = TarifacaoService(
        utilizadores, preco_bloco_centimos=preco_bloco_centimos
    )
    cobranca = CobrancaService(db_path, utilizadores)
    viagens = ViagensService(db_path, tarifacao, cobranca)
    docas = ComunicacaoDocasService(
        db_path, viagens, prazo_retirada_segundos=prazo_retirada_segundos,
        timeout_comando_segundos=timeout_comando_segundos
    )
    desbloqueio = DesbloqueioService(utilizadores, viagens, docas)

    for componente in (utilizadores, cobranca, viagens, docas):
        componente.init_schema()

    return {
        "utilizadores": utilizadores,
        "tarifacao": tarifacao,
        "cobranca": cobranca,
        "viagens": viagens,
        "docas": docas,
        "desbloqueio": desbloqueio,
    }
