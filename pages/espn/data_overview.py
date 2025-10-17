import streamlit as st
import pandas as pd

def data_overview_tab():
    cols = st.columns(5)
    with cols[0]:
        uploaded_dst = st.file_uploader("Upload New DST CSV from FantasyPros", type="csv", key="dst_uploader")
        if uploaded_dst:
            st.session_state["dst_data"] = pd.read_csv(uploaded_dst)
    with cols[1]:
        uploaded_flx = st.file_uploader("Upload New FLX CSV from FantasyPros", type="csv", key="flx_uploader")
        if uploaded_flx:
            st.session_state["flx_data"] = pd.read_csv(uploaded_flx)
    with cols[2]:
        uploaded_k = st.file_uploader("Upload New K CSV from FantasyPros", type="csv", key="k_uploader")
        if uploaded_k:
            st.session_state["k_data"] = pd.read_csv(uploaded_k)
    with cols[3]:
        uploaded_qb = st.file_uploader("Upload New QB CSV from FantasyPros", type="csv", key="qb_uploader")
        if uploaded_qb:
            st.session_state["qb_data"] = pd.read_csv(uploaded_qb)
    with cols[4]:
        uploaded_adp = st.file_uploader("Upload New ADP CSV from FantasyPros", type="csv", key="adp_uploader")
        if uploaded_adp:
            st.session_state["adp_data"] = pd.read_csv(uploaded_adp)

    data_tabs = st.tabs(["DST", "FLX", "K", "QB", "ADP"])

    with data_tabs[0]:
        st.header("DST Input Data")
        st.dataframe(st.session_state["dst_data"])

    with data_tabs[1]:
        st.header("FLX Input Data")
        st.dataframe(st.session_state["flx_data"])

    with data_tabs[2]:
        st.header("K Input Data")
        st.dataframe(st.session_state["k_data"])

    with data_tabs[3]:
        st.header("QB Input Data")
        st.dataframe(st.session_state["qb_data"])

    with data_tabs[4]:
        st.header("ADP Input Data")
        st.dataframe(st.session_state["adp_data"])

    combined_data = st.session_state["combined_data"]

    st.markdown("---")
    st.header("Combined Player Data with Fantasy Points")
    st.dataframe(combined_data)

    st.markdown("---")
    st.header("Position Rankings")

    unique_positions = combined_data["POS"].unique()

    columns = st.columns(len(unique_positions))

    for position, col in zip(unique_positions, columns):
        with col:
            st.subheader(position)
            st.dataframe(combined_data[combined_data["POS"] == position].sort_values(by="FPTS_Rank"), hide_index=True)

st.set_page_config(page_title="Data Overview", layout="wide")
data_overview_tab()
