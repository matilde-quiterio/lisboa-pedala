from datetime import datetime
from decimal import Decimal
from typing import Protocol


class TarifacaoPort(Protocol):

    def calcular(
        self,
        *,
        viagem_id: str,
        utilizador_id: str,
        bicicleta_id: str,
        inicio: datetime,
        fim: datetime,
    ) -> Decimal:
        """
        Calcula a tarifa da viagem.

        A fórmula e a forma concreta de obter a configuração
        municipal ainda não estão definidas nos ficheiros.
        """
        ...