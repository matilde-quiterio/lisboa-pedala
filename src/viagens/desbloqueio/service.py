class DesbloqueioService:
    def __init__(self, utilizadores, viagens, comunicacao_docas):
        self.utilizadores = utilizadores
        self.viagens = viagens
        self.comunicacao_docas = comunicacao_docas

    def desbloquear(
        self,
        *,
        utilizador_id: str,
        bicicleta_id: str,
        doca_id: str,
        meio_pagamento: str,
        mbway_numero: str | None,
        resultado_fisico_doca: str,
        atraso_resposta_segundos: float = 0,
        agora=None,
    ) -> dict:
        if not self.utilizadores.validar(utilizador_id):
            return {"estado": "REJEITADO", "motivo": "utilizador inexistente ou inativo"}

        preparada = self.viagens.preparar_viagem(
            utilizador_id=utilizador_id,
            bicicleta_id=bicicleta_id,
            meio_pagamento=meio_pagamento,
            mbway_numero=mbway_numero,
        )

        resultado = self.comunicacao_docas.destrancar(
            doca_id=doca_id,
            bicicleta_id=bicicleta_id,
            utilizacao_id=preparada["utilizacao_id"],
            resultado_fisico=resultado_fisico_doca,
            atraso_resposta_segundos=atraso_resposta_segundos,
            agora=agora,
        )

        if resultado == "FALHA":
            self.viagens.cancelar_pendente(preparada["utilizacao_id"])
            return {**preparada, "estado": "FALHOU"}
        if resultado == "TIMEOUT":
            # Timeout não prova falha física; mantém PENDENTE.
            return {**preparada, "estado": "POR_CONFIRMAR"}
        return {**preparada, "estado": "DESTRANCADA"}
