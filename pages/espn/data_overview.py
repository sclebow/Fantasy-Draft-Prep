import streamlit as st
from scraper.fantasypros_scraper import update_session_state_with_scraped_data

def data_overview_tab():
    if st.button("Scrape Latest FantasyPros Data"):
        update_session_state_with_scraped_data()
        st.success("Data scraped and session state updated.")

    if "qb_data" not in st.session_state and \
       "flx_data" not in st.session_state and \
       "dst_data" not in st.session_state and \
       "k_data" not in st.session_state:
        st.info("No data scraped yet. Click the button above to scrape projections from FantasyPros.")
        return

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
