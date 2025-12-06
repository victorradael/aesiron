import streamlit as st

from core.settings import Settings
from ui.components import select_topic

settings = Settings()

app_name = settings.app_name
st.set_page_config(page_title=f"App {app_name}", layout="centered")
st.title(f"📡 {app_name}")

select_topic(["Option 1", "Option 2", "Option 3"])
