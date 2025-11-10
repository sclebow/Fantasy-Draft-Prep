import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd

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

@st.cache_data(ttl=86400) # Cache for 1 day
def update_session_state_with_scraped_data():
    qb_projections_url = "https://www.fantasypros.com/nfl/projections/qb.php?week=draft"
    flx_projections_url = "https://www.fantasypros.com/nfl/projections/flex.php?week=draft"
    dst_projections_url = "https://www.fantasypros.com/nfl/projections/dst.php?week=draft"
    k_projections_url = "https://www.fantasypros.com/nfl/projections/k.php?week=draft"
    adp_projections_url = "https://www.fantasypros.com/nfl/adp/overall.php"

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

