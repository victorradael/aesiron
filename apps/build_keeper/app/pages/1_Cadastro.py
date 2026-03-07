import streamlit as st
from core.settings import Settings
from core.logger import get_logger
from ui.views import render_registration_screen

settings = Settings()
logger = get_logger(__name__)

app_name = settings.app_name
st.set_page_config(page_title=f"Cadastro - {app_name}", layout="centered")
st.title("Cadastro de Conjunto")

logger.info("Renderizando tela: Cadastro de Conjunto")
render_registration_screen()
