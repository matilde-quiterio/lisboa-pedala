from datetime import datetime
import math


class TarifacaoService:
    GRATUITO_SEGUNDOS_PASSE_ANUAL = 45 * 60
    BLOCO_SEGUNDOS = 15 * 60

    def __init__(self, utilizadores, *, preco_bloco_centimos: int):
        if preco_bloco_centimos < 0:
            raise ValueError("preco_bloco_centimos tem de ser >= 0")
        self.utilizadores = utilizadores
        self.preco_bloco_centimos = preco_bloco_centimos

    def calcular(self, utilizador_id: str, inicio_iso: str, fim_iso: str) -> int:
        tipo_plano = self.utilizadores.obter_tipo_plano(utilizador_id)
        if tipo_plano != "PASSE_ANUAL":
            raise ValueError(
                "Os ficheiros fornecidos só definem a regra tarifária da US-1 "
                "para assinantes com PASSE_ANUAL."
            )

        inicio = datetime.fromisoformat(inicio_iso)
        fim = datetime.fromisoformat(fim_iso)
        duracao = (fim - inicio).total_seconds()
        if duracao < 0:
            raise ValueError("fim físico não pode ser anterior ao início físico")
        if duracao <= self.GRATUITO_SEGUNDOS_PASSE_ANUAL:
            return 0
        excedente = duracao - self.GRATUITO_SEGUNDOS_PASSE_ANUAL
        blocos = math.ceil(excedente / self.BLOCO_SEGUNDOS)
        return blocos * self.preco_bloco_centimos
