import os
import logging

logging.basicConfig(
    level=logging.INFO,  # Nível de log (debug, info, warning, error, critical)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Formato da mensagem
    handlers=[
        logging.StreamHandler(),  # Exibe no console
        logging.FileHandler("app.log"),  # Salva em um arquivo de log
    ],
)

logger = logging.getLogger(__name__)


class Settings:
    def __init__(self):
        self.app_name = os.getenv("APP_NAME", "undefined")

        logger.info(f"APP_NAME: {self.app_name}")
