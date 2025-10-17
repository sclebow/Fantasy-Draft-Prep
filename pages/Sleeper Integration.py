import streamlit as st
from tabs.sleeper_integration import sleeper_integration_tab

st.set_page_config(page_title="Sleeper Integration", layout="wide")
sleeper_integration_tab()
