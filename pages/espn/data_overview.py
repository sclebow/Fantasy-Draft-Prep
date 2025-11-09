from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def wait_seconds(seconds):
    print(f"Waiting for {seconds} seconds...")
    for i in range(seconds):
        time.sleep(1)
        print(f"Waiting... {i + 1}/{seconds} seconds elapsed.")

def scrape_projections_df(projections_url):
    """
    Scrape the projections DataFrame from FantasyPros using Selenium and save it locally.
    """

    import requests

    print(f"Requesting {projections_url} ...")
    response = requests.get(projections_url)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", id="data")
    if table is None:
        print("Table not found.")
        return None

    # Parse table into DataFrame
    df = pd.read_html(str(table))[0]

    # Check if there are multiple header rows and only keep the last one
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(-1)

    # Rename duplicate columns to make them unique
    def make_unique_columns(columns):
        counts = {}
        new_cols = []
        for col in columns:
            if col in counts:
                counts[col] += 1
                new_cols.append(f"{col}_{counts[col]}")
            else:
                counts[col] = 0
                new_cols.append(col)
        return new_cols
    df.columns = make_unique_columns(df.columns)

    return df

def data_overview_tab():
    st.header("FantasyPros Scrape Attempt")

    qb_projections_url = "https://www.fantasypros.com/nfl/projections/qb.php?week=draft"
    flx_projections_url = "https://www.fantasypros.com/nfl/projections/flex.php?week=draft"
    dst_projections_url = "https://www.fantasypros.com/nfl/projections/dst.php?week=draft"
    k_projections_url = "https://www.fantasypros.com/nfl/projections/k.php?week=draft"
    adp_projections_url = "https://www.fantasypros.com/nfl/adp/overall.php"

    scrape_button = st.button("Scrape Projections from FantasyPros")

    if scrape_button:
        with st.spinner("Scraping QB projections..."):
            qb_df = scrape_projections_df(qb_projections_url)
            st.session_state["qb_data"] = qb_df

        with st.spinner("Scraping FLX projections..."):
            flx_df = scrape_projections_df(flx_projections_url)
            st.session_state["flx_data"] = flx_df

        with st.spinner("Scraping DST projections..."):
            dst_df = scrape_projections_df(dst_projections_url)
            st.session_state["dst_data"] = dst_df

        with st.spinner("Scraping K projections..."):
            k_df = scrape_projections_df(k_projections_url)
            st.session_state["k_data"] = k_df

        with st.spinner("Scraping ADP data..."):
            adp_df = scrape_projections_df(adp_projections_url)
            st.session_state["adp_data"] = adp_df

    st.markdown("---")

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
