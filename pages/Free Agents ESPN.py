import streamlit as st
from tabs.free_agents_espn import free_agents_espn_tab

st.set_page_config(page_title="Free Agents in ESPN", layout="wide")
free_agents_espn_tab()
