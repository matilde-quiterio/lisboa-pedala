from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol


@dataclass(frozen=True)
class ResultadoCobranca:
    sucesso: bool
    referencia: str | None = None
    motivo: str | None = None


class CobrancaPort(Protocol):

    def cobrar(
        self,
        *,
        utilizador_id: str,
        valor: Decimal,
        metodo_pagamento: str,
        dados_pagamento: dict[str, Any] | None,
        chave_idempotencia: str,
    ) -> ResultadoCobranca:
        ...