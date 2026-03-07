import os

from core.logger import get_logger

logger = get_logger(__name__)


class Settings:
    def __init__(self):
        self.app_name = os.getenv("APP_NAME", "undefined")

        logger.info(f"APP_NAME: {self.app_name}")
