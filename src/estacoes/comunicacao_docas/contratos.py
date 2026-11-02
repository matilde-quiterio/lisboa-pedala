from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class EstadoDesbloqueio(str, Enum):
    CONFIRMADO = "CONFIRMADO"
    FALHOU = "FALHOU"
    POR_CONFIRMAR = "POR_CONFIRMAR"


@dataclass(frozen=True)
class ResultadoDesbloqueio:
    estado: EstadoDesbloqueio


class ComunicacaoDocasPort(Protocol):

    def desbloquear(
        self,
        *,
        bicicleta_id: str,
        viagem_id: str,
    ) -> ResultadoDesbloqueio:
        ...