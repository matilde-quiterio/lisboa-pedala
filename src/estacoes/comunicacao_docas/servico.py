from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.viagens.viagens.servico import ViagensService


class TipoEventoDoca(str, Enum):
    RETIRADA = "RETIRADA"
    DEVOLUCAO = "DEVOLUCAO"


@dataclass(frozen=True)
class EventoDoca:
    id: str
    tipo: TipoEventoDoca
    bicicleta_id: str
    estacao_id: str
    instante_fisico: datetime


class ComunicacaoDocasService:

    def __init__(
        self,
        viagens: ViagensService,
    ):
        self.viagens = viagens

    def receber_evento(
        self,
        evento: EventoDoca,
    ) -> None:

        if evento.tipo == TipoEventoDoca.RETIRADA:

            self.viagens.registar_retirada(
                evento_id=evento.id,
                bicicleta_id=evento.bicicleta_id,
                estacao_id=evento.estacao_id,
                instante_fisico=evento.instante_fisico,
            )

            return

        if evento.tipo == TipoEventoDoca.DEVOLUCAO:

            self.viagens.registar_devolucao(
                evento_id=evento.id,
                bicicleta_id=evento.bicicleta_id,
                estacao_id=evento.estacao_id,
                instante_fisico=evento.instante_fisico,
            )

            return

        raise ValueError(
            f"Tipo de evento desconhecido: {evento.tipo}"
        )