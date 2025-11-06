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

def scrape_qb_projections_csv(qb_projections_url, fantasy_pros_username, fantasy_pros_password, download_dir="/tmp"):
    """
    Scrape the QB projections CSV from FantasyPros using Selenium and save it locally.
    Returns the path to the downloaded CSV file.
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import glob

    print("Starting Selenium WebDriver...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    driver.get(qb_projections_url)
    print(f"Navigated to {qb_projections_url}")

    # Wait for the table to load
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "data"))
        )
        print("Table loaded.")
    except Exception as e:
        print("Error locating table:", e)
        driver.quit()
        return None

    # Get page source and parse table
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find("table", id="data")
    if table is None:
        print("Table not found.")
        driver.quit()
        return None

    # Parse table into DataFrame
    df = pd.read_html(str(table))[0]
    driver.quit()
    return df
    #             )
    #             download_button.click()
    #             print("Download button clicked after login.")

    #             # Wait again for the CSV file to appear in the download directory
    #             for _ in range(30):  # Wait up to 30 seconds
    #                 files = glob.glob(os.path.join(download_dir, "*.csv"))
    #                 if files:
    #                     csv_path = max(files, key=os.path.getmtime)
    #                     break
    #                 time.sleep(1)
    #                 print(f"Waiting for CSV file... {_ + 1}/30 seconds elapsed.")
    #             if not csv_path:
    #                 print("CSV file still not found after login.")

    #         except Exception as e:
    #             print("Login failed:", e)

    # except Exception as e:
    #     csv_path = None
    #     print(f"Error during scraping: {e}")
    # driver.quit()
    # return csv_path

def data_overview_tab():
    st.header("FantasyPros Scrape Attempt")

    qb_projections_url = "https://www.fantasypros.com/nfl/projections/qb.php?week=draft"
    rb_projections_url = "https://www.fantasypros.com/nfl/projections/rb.php?week=draft"
    wr_projections_url = "https://www.fantasypros.com/nfl/projections/wr.php?week=draft"
    te_projections_url = "https://www.fantasypros.com/nfl/projections/te.php?week=draft"
    k_projections_url = "https://www.fantasypros.com/nfl/projections/k.php?week=draft"
    dst_projections_url = "https://www.fantasypros.com/nfl/projections/dst.php?week=draft"

    # Scrape QB projections CSV and load into DataFrame
    cols = st.columns(3)

    with cols[0]:
        fantasy_pros_username = st.text_input("FantasyPros Username", key="fp_username")
    with cols[1]:
        fantasy_pros_password = st.text_input("FantasyPros Password", type="password", key="fp_password")
    with cols[2]:
        scrape_button = st.button("Scrape QB Projections CSV from FantasyPros")

    if scrape_button:
        csv_path = scrape_qb_projections_csv(qb_projections_url, fantasy_pros_username, fantasy_pros_password)
        if csv_path:
            st.success(f"Downloaded QB projections CSV: {csv_path}")
            qb_df = pd.read_csv(csv_path)
            st.dataframe(qb_df)
        else:
            st.error("Failed to download QB projections CSV.")

    st.markdown("---")

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
