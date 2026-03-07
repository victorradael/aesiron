import streamlit as st


def select_topic(topics):
    return st.selectbox("Select a topic", topics, key="topics")
