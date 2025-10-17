import streamlit as st
from tabs.live_draft import live_draft_tab

st.set_page_config(page_title="Live Draft", layout="wide")
live_draft_tab()
