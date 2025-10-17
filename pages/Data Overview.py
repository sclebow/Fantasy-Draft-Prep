import streamlit as st
from tabs.data_overview import data_overview_tab

st.set_page_config(page_title="Data Overview", layout="wide")
data_overview_tab()
