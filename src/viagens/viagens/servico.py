from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from src.viagens.cobranca.contratos import CobrancaPort
from src.viagens.tarifacao.contratos import TarifacaoPort

from .modelos import EstadoViagem, Viagem
from .repositorio import RepositorioViagensSQLite


class ViagemNaoEncontrada(Exception):
    pass


class ViagemNaoPermitida(Exception):
    pass


class ViagensService:

    def __init__(
        self,
        repositorio: RepositorioViagensSQLite,
        tarifacao: TarifacaoPort,
        cobranca: CobrancaPort,
    ):
        self.repositorio = repositorio
        self.tarifacao = tarifacao
        self.cobranca = cobranca

    def preparar_viagem(
        self,
        *,
        utilizador_id: str,
        bicicleta_id: str,
        metodo_pagamento: str,
        dados_pagamento: dict | None,
        instante_pedido: datetime,
    ) -> str:

        with self.repositorio.transacao() as conn:

            if self.repositorio.existe_viagem_ativa_utilizador(
                conn,
                utilizador_id,
            ):
                raise ViagemNaoPermitida(
                    "O utilizador já possui uma viagem "
                    "PENDENTE ou EM_CURSO."
                )

            if self.repositorio.existe_viagem_ativa_bicicleta(
                conn,
                bicicleta_id,
            ):
                raise ViagemNaoPermitida(
                    "A bicicleta já possui uma viagem "
                    "PENDENTE ou EM_CURSO."
                )

            viagem = Viagem(
                id=str(uuid4()),
                utilizador_id=utilizador_id,
                bicicleta_id=bicicleta_id,
                estado=EstadoViagem.PENDENTE,
                criada_em=instante_pedido,
                metodo_pagamento=metodo_pagamento,
                dados_pagamento=dados_pagamento,
            )

            self.repositorio.guardar(conn, viagem)

            return viagem.id

    def cancelar_pendente(
        self,
        viagem_id: str,
    ) -> None:

        with self.repositorio.transacao() as conn:

            viagem = self.repositorio.obter_por_id(
                conn,
                viagem_id,
            )

            if viagem is None:
                raise ViagemNaoEncontrada(viagem_id)

            if viagem.estado != EstadoViagem.PENDENTE:
                return

            viagem.estado = EstadoViagem.CANCELADA

            self.repositorio.guardar(conn, viagem)

    def registar_retirada(
        self,
        *,
        evento_id: str,
        bicicleta_id: str,
        estacao_id: str,
        instante_fisico: datetime,
    ) -> None:

        finalizar = False
        viagem_id = None

        with self.repositorio.transacao() as conn:

            if self.repositorio.evento_ja_processado(
                conn,
                evento_id,
            ):
                return

            viagem = (
                self.repositorio.obter_aberta_por_bicicleta(
                    conn,
                    bicicleta_id,
                )
            )

            if viagem is None:
                raise ViagemNaoEncontrada(
                    f"Não existe viagem aberta para "
                    f"{bicicleta_id}."
                )

            if instante_fisico < viagem.criada_em:
                raise ValueError(
                    "O evento é anterior à viagem."
                )

            viagem.evento_retirada_id = evento_id
            viagem.inicio = instante_fisico
            viagem.estacao_inicio_id = estacao_id
            viagem.estado = EstadoViagem.EM_CURSO

            # A devolução pode ter chegado antes.
            if viagem.devolucao_pendente_em is not None:

                if (
                    viagem.devolucao_pendente_em
                    < instante_fisico
                ):
                    raise ValueError(
                        "A devolução ocorreu antes da retirada."
                    )

                viagem.fim = viagem.devolucao_pendente_em
                viagem.estado = EstadoViagem.TERMINADA

                finalizar = True
                viagem_id = viagem.id

            self.repositorio.guardar(conn, viagem)

            # Evento + alteração da viagem:
            # mesma transação.
            self.repositorio.marcar_evento_processado(
                conn,
                evento_id,
                viagem.id,
            )

        if finalizar:
            self.processar_viagem_terminada(viagem_id)

    def registar_devolucao(
        self,
        *,
        evento_id: str,
        bicicleta_id: str,
        estacao_id: str,
        instante_fisico: datetime,
    ) -> None:

        finalizar = False
        viagem_id = None

        with self.repositorio.transacao() as conn:

            if self.repositorio.evento_ja_processado(
                conn,
                evento_id,
            ):
                return

            viagem = (
                self.repositorio.obter_aberta_por_bicicleta(
                    conn,
                    bicicleta_id,
                )
            )

            if viagem is None:
                raise ViagemNaoEncontrada(
                    f"Não existe viagem aberta para "
                    f"{bicicleta_id}."
                )

            if instante_fisico < viagem.criada_em:
                raise ValueError(
                    "O evento é anterior à viagem."
                )

            viagem.evento_devolucao_id = evento_id
            viagem.estacao_fim_id = estacao_id

            if viagem.inicio is None:

                # A devolução chegou primeiro.
                viagem.devolucao_pendente_em = (
                    instante_fisico
                )

            else:

                if instante_fisico < viagem.inicio:
                    raise ValueError(
                        "A devolução ocorreu antes da retirada."
                    )

                viagem.fim = instante_fisico
                viagem.estado = EstadoViagem.TERMINADA

                finalizar = True
                viagem_id = viagem.id

            self.repositorio.guardar(conn, viagem)

            self.repositorio.marcar_evento_processado(
                conn,
                evento_id,
                viagem.id,
            )

        # O fecho já foi confirmado na BD.
        if finalizar:
            self.processar_viagem_terminada(viagem_id)

    def processar_viagem_terminada(
        self,
        viagem_id: str,
    ) -> None:

        viagem = (
            self.repositorio.obter_por_id_fora_transacao(
                viagem_id
            )
        )

        if viagem is None:
            raise ViagemNaoEncontrada(viagem_id)

        if viagem.estado != EstadoViagem.TERMINADA:
            raise ValueError(
                "A viagem ainda não está terminada."
            )

        if viagem.inicio is None or viagem.fim is None:
            raise ValueError(
                "A viagem não possui início e fim."
            )

        # Se a tarifa já estiver guardada,
        # não é necessário voltar a calculá-la.
        if viagem.tarifa is None:

            tarifa = self.tarifacao.calcular(
                viagem_id=viagem.id,
                utilizador_id=viagem.utilizador_id,
                bicicleta_id=viagem.bicicleta_id,
                inicio=viagem.inicio,
                fim=viagem.fim,
            )

            with self.repositorio.transacao() as conn:
                atual = self.repositorio.obter_por_id(
                    conn,
                    viagem.id,
                )

                atual.tarifa = tarifa

                self.repositorio.guardar(
                    conn,
                    atual,
                )

            viagem.tarifa = tarifa

        if viagem.tarifa == Decimal("0"):
            return

        if viagem.cobranca_concluida:
            return

        resultado = self.cobranca.cobrar(
            utilizador_id=viagem.utilizador_id,
            valor=viagem.tarifa,
            metodo_pagamento=viagem.metodo_pagamento,
            dados_pagamento=viagem.dados_pagamento,
            chave_idempotencia=f"viagem:{viagem.id}",
        )

        if resultado.sucesso:

            with self.repositorio.transacao() as conn:
                atual = self.repositorio.obter_por_id(
                    conn,
                    viagem.id,
                )

                atual.cobranca_concluida = True

                self.repositorio.guardar(
                    conn,
                    atual,
                )