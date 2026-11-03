from datetime import datetime, timedelta, timezone

from bootstrap import criar_aplicacao
from src.estacoes.comunicacao_docas.service import ResultadoDestrancamento


def app(tmp_path, preco=200, prazo=60):
    a = criar_aplicacao(
        str(tmp_path / "db.sqlite"),
        preco_bloco_centimos=preco,
        prazo_retirada_segundos=prazo,
        timeout_comando_segundos=2,
    )
    a["utilizadores"].adicionar_ficticio(
        "u1", ativo=True, tipo_plano="PASSE_ANUAL", referencia_cartao="card-ref-1"
    )
    a["docas"].registar_doca("d1", "b1")
    a["docas"].registar_doca("d2")
    return a


def iniciar(a, t0, meio="CARTAO_ASSOCIADO", mbway=None):
    return a["desbloqueio"].desbloquear(
        utilizador_id="u1",
        bicicleta_id="b1",
        doca_id="d1",
        meio_pagamento=meio,
        mbway_numero=mbway,
        resultado_fisico_doca=ResultadoDestrancamento.SUCESSO,
        agora=t0,
    )


def test_fluxo_feliz_gratuito(tmp_path):
    a = app(tmp_path)
    t0 = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    r = iniciar(a, t0)
    assert a["viagens"].obter_por_utilizacao(r["utilizacao_id"])["estado"] == "PENDENTE"

    a["docas"].retirada_fisica("d1", instante=t0 + timedelta(seconds=10))
    assert a["viagens"].obter_por_utilizacao(r["utilizacao_id"])["estado"] == "EM_CURSO"

    a["docas"].encaixe_fisico(
        doca_id="d2", bicicleta_id="b1", utilizacao_id=r["utilizacao_id"],
        instante=t0 + timedelta(minutes=40)
    )
    v = a["viagens"].obter_por_utilizacao(r["utilizacao_id"])
    assert v["estado"] == "TERMINADA"
    assert v["tarifa_centimos"] == 0
    assert v["estado_cobranca"] is None


def test_tarifa_blocos_e_cobranca_mbway(tmp_path):
    a = app(tmp_path, preco=175)
    t0 = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    r = iniciar(a, t0, meio="MBWAY", mbway="910000000")
    a["docas"].retirada_fisica("d1", instante=t0)
    a["docas"].encaixe_fisico(
        doca_id="d2", bicicleta_id="b1", utilizacao_id=r["utilizacao_id"],
        instante=t0 + timedelta(minutes=60, seconds=1)
    )
    v = a["viagens"].obter_por_utilizacao(r["utilizacao_id"])
    assert v["tarifa_centimos"] == 350  # >60 min => 2 blocos iniciados após os 45 min
    assert v["estado_cobranca"] == "ACEITE"


def test_falha_destrancamento_cancela_pendente(tmp_path):
    a = app(tmp_path)
    t0 = datetime.now(timezone.utc)
    r = a["desbloqueio"].desbloquear(
        utilizador_id="u1", bicicleta_id="b1", doca_id="d1",
        meio_pagamento="CARTAO_ASSOCIADO", mbway_numero=None,
        resultado_fisico_doca=ResultadoDestrancamento.FALHA, agora=t0,
    )
    assert r["estado"] == "FALHOU"
    assert a["viagens"].obter_por_utilizacao(r["utilizacao_id"])["estado"] == "CANCELADA"


def test_timeout_mantem_pendente(tmp_path):
    a = app(tmp_path)
    r = a["desbloqueio"].desbloquear(
        utilizador_id="u1", bicicleta_id="b1", doca_id="d1",
        meio_pagamento="CARTAO_ASSOCIADO", mbway_numero=None,
        resultado_fisico_doca=ResultadoDestrancamento.SUCESSO, atraso_resposta_segundos=3,
    )
    assert r["estado"] == "POR_CONFIRMAR"
    assert a["viagens"].obter_por_utilizacao(r["utilizacao_id"])["estado"] == "PENDENTE"


def test_prazo_retirada_rebloqueia_localmente_mesmo_offline(tmp_path):
    a = app(tmp_path, prazo=30)
    t0 = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    r = iniciar(a, t0)
    a["docas"].definir_online("d1", False, agora=t0 + timedelta(seconds=1))
    a["docas"].processar_prazos(agora=t0 + timedelta(seconds=31))
    # backend ainda não recebeu confirmação porque a doca está offline
    assert a["viagens"].obter_por_utilizacao(r["utilizacao_id"])["estado"] == "PENDENTE"
    a["docas"].definir_online("d1", True, agora=t0 + timedelta(seconds=40))
    assert a["viagens"].obter_por_utilizacao(r["utilizacao_id"])["estado"] == "CANCELADA"


def test_devolucao_antes_da_retirada_e_eventos_fisicos(tmp_path):
    a = app(tmp_path)
    t0 = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    r = iniciar(a, t0)
    # Simula receção fora de ordem diretamente pelo contrato Comunicação Docas -> Viagens.
    a["viagens"].processar_evento_doca(
        evento_id="e-end", utilizacao_id=r["utilizacao_id"], tipo="ENCAIXE",
        bicicleta_id="b1", doca_id="d2",
        instante_fisico=(t0 + timedelta(minutes=50)).isoformat(),
    )
    assert a["viagens"].obter_por_utilizacao(r["utilizacao_id"])["estado"] == "PENDENTE"
    a["viagens"].processar_evento_doca(
        evento_id="e-start", utilizacao_id=r["utilizacao_id"], tipo="RETIRADA",
        bicicleta_id="b1", doca_id="d1",
        instante_fisico=t0.isoformat(),
    )
    v = a["viagens"].obter_por_utilizacao(r["utilizacao_id"])
    assert v["estado"] == "TERMINADA"
    assert v["inicio_fisico"] == t0.isoformat()
    assert v["fim_fisico"] == (t0 + timedelta(minutes=50)).isoformat()


def test_evento_repetido_nao_duplica_efeito(tmp_path):
    a = app(tmp_path)
    t0 = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    r = iniciar(a, t0)
    kwargs = dict(
        evento_id="same", utilizacao_id=r["utilizacao_id"], tipo="RETIRADA",
        bicicleta_id="b1", doca_id="d1", instante_fisico=t0.isoformat(),
    )
    first = a["viagens"].processar_evento_doca(**kwargs)
    second = a["viagens"].processar_evento_doca(**kwargs)
    assert first["duplicado"] is False
    assert second["duplicado"] is True
    assert a["viagens"].obter_por_utilizacao(r["utilizacao_id"])["inicio_fisico"] == t0.isoformat()

def test_retry_conclusao_nao_reprocessa_evento(tmp_path):
    a = app(tmp_path, preco=175)

    t0 = datetime(
        2026, 1, 1, 8, 0,
        tzinfo=timezone.utc,
    )

    # MB WAY sem número -> cobrança falha.
    r = iniciar(
        a,
        t0,
        meio="MBWAY",
        mbway=None,
    )

    a["docas"].retirada_fisica(
        "d1",
        instante=t0,
    )

    a["docas"].encaixe_fisico(
        doca_id="d2",
        bicicleta_id="b1",
        utilizacao_id=r["utilizacao_id"],
        instante=t0 + timedelta(minutes=50),
    )

    v = a["viagens"].obter_por_utilizacao(
        r["utilizacao_id"]
    )

    assert v["estado"] == "TERMINADA"
    assert v["estado_cobranca"] == "FALHOU"

    # Retry sem reprocessar o evento ENCAIXE.
    v = a["viagens"].reprocessar_conclusao(
        r["utilizacao_id"]
    )

    assert v["estado"] == "TERMINADA"
    assert v["estado_cobranca"] == "FALHOU"