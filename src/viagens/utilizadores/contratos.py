from typing import Protocol


class UtilizadoresPort(Protocol):

    def validar_acesso(self, utilizador_id: str) -> bool:
        """
        Indica se o utilizador está autorizado a iniciar uma viagem.

        As regras concretas de autorização não estão definidas
        nos ficheiros fornecidos.
        """
        ...