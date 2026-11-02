from dataclasses import dataclass
from datetime import datetime

from src.estacoes.comunicacao_docas.contratos import (
    ComunicacaoDocasPort,
    EstadoDesbloqueio,
)
from src.viagens.utilizadores.contratos import (
    UtilizadoresPort,
)
from src.viagens.viagens.servico import (
    ViagensService,
)


class UtilizadorNaoAutorizado(Exception):
    pass


@dataclass(frozen=True)
class ResultadoPedidoDesbloqueio:
    viagem_id: str
    estado: EstadoDesbloqueio


class DesbloqueioService:

    def __init__(
        self,
        utilizadores: UtilizadoresPort,
        viagens: ViagensService,
        comunicacao_docas: ComunicacaoDocasPort,
    ):
        self.utilizadores = utilizadores
        self.viagens = viagens
        self.comunicacao_docas = comunicacao_docas

    def desbloquear(
        self,
        *,
        utilizador_id: str,
        bicicleta_id: str,
        metodo_pagamento: str,
        dados_pagamento: dict | None,
        instante_pedido: datetime,
    ) -> ResultadoPedidoDesbloqueio:

        # 1. Validar utilizador.
        if not self.utilizadores.validar_acesso(
            utilizador_id
        ):
            raise UtilizadorNaoAutorizado(
                "Utilizador não autorizado."
            )

        # 2. Guardar viagem PENDENTE ANTES
        #    do comando físico.
        viagem_id = self.viagens.preparar_viagem(
            utilizador_id=utilizador_id,
            bicicleta_id=bicicleta_id,
            metodo_pagamento=metodo_pagamento,
            dados_pagamento=dados_pagamento,
            instante_pedido=instante_pedido,
        )

        # 3. Só agora solicitar o destrancamento.
        resultado = self.comunicacao_docas.desbloquear(
            bicicleta_id=bicicleta_id,
            viagem_id=viagem_id,
        )

        # Falha física confirmada:
        # cancelar o registo PENDENTE.
        if resultado.estado == EstadoDesbloqueio.FALHOU:

            self.viagens.cancelar_pendente(
                viagem_id
            )

        # POR_CONFIRMAR:
        # mantém PENDENTE.

        return ResultadoPedidoDesbloqueio(
            viagem_id=viagem_id,
            estado=resultado.estado,
        )