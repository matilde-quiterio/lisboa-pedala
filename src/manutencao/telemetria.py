import uuid
from datetime import datetime
from typing import Callable, Dict, Any

class TelemetriaService:
    def __init__(self, publicar_callback: Callable[[Dict[str, Any]], None]):
        self.publicar_callback = publicar_callback

    def receber_telemetria(self, bicicleta_id: str, tem_avaria: bool, codigo_avaria: str = "", descricao: str = "") -> None:
        """Publica mensagem assíncrona no broker se existir avaria."""
        if tem_avaria:
            mensagem = {
                "mensagem_id": str(uuid.uuid4()),
                "bicicleta_id": bicicleta_id,
                "codigo_avaria": codigo_avaria,
                "descricao": descricao,
                "timestamp": datetime.now().isoformat()
            }
            self.publicar_callback(mensagem)