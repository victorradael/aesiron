import streamlit as st

from core.settings import Settings
from ui.views import render_registration_screen, render_checklist_screen

settings = Settings()

app_name = settings.app_name
st.set_page_config(page_title=f"App {app_name}", layout="centered")
st.title(f"{app_name}")

st.sidebar.title("Navegação")
option = st.sidebar.radio(
    "Escolha a tela:", ("Cadastro de Conjunto", "Checklist de Equipamentos")
)

if option == "Cadastro de Conjunto":
    render_registration_screen()
elif option == "Checklist de Equipamentos":
    render_checklist_screen()
