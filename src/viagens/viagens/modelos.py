from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class EstadoViagem(str, Enum):
    PENDENTE = "PENDENTE"
    EM_CURSO = "EM_CURSO"
    TERMINADA = "TERMINADA"
    CANCELADA = "CANCELADA"


@dataclass
class Viagem:
    id: str
    utilizador_id: str
    bicicleta_id: str
    estado: EstadoViagem
    criada_em: datetime

    inicio: datetime | None = None
    fim: datetime | None = None

    estacao_inicio_id: str | None = None
    estacao_fim_id: str | None = None

    metodo_pagamento: str | None = None
    dados_pagamento: dict[str, Any] | None = None

    tarifa: Decimal | None = None
    cobranca_concluida: bool = False

    evento_retirada_id: str | None = None
    evento_devolucao_id: str | None = None

    devolucao_pendente_em: datetime | None = None