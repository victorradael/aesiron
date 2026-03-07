import streamlit as st

from core.settings import Settings
from core.logger import get_logger
from ui.components import select_topic

settings = Settings()
logger = get_logger(__name__)

app_name = settings.app_name
st.set_page_config(page_title=f"App {app_name}", layout="centered")
st.title(f"📡 {app_name}")

logger.info("Página principal carregada.")

select_topic(["Option 1", "Option 2", "Option 3"])
