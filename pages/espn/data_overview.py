import streamlit as st
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import time


def scrape_qb_projections_csv(qb_projections_url, download_dir="/tmp"):
    """
    Scrape the QB projections CSV from FantasyPros using Selenium and save it locally.
    Returns the path to the downloaded CSV file.
    """
    # Set up Selenium WebDriver (Chrome)
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": download_dir}
    options.add_experimental_option("prefs", prefs)
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "profile.default_content_settings.popups": 0,
        "directory_upgrade": True
    })
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(qb_projections_url)
    time.sleep(2)
    # Close cookie acceptance banner if present
    try:
        cookie_btn = driver.find_element(By.XPATH, "//*[@id='onetrust-accept-btn-handler']")
        cookie_btn.click()
        time.sleep(1)
        print("Cookie banner closed.")
    except Exception as e:
        print("No cookie banner to close or error:", e)
    # Find the CSV download button (usually contains 'CSV' text)
    try:
        download_button = driver.find_element(By.XPATH, "/html/body/div[2]/div[3]/div/div[1]/div/div[1]/div[2]/div/a[2]")
        download_button.click()
        time.sleep(5)  # Wait for download
        # Find the most recent CSV file in download_dir
        files = [f for f in os.listdir(download_dir) if f.endswith('.csv')]
        if files:
            csv_path = os.path.join(download_dir, sorted(files, key=lambda x: os.path.getmtime(os.path.join(download_dir, x)), reverse=True)[0])
        else:
            csv_path = None

        if not csv_path:
            # This is because we need to log into FantasyPros to access the CSV
            # TODO: Implement login logic here if necessary
            pass # TODO
    except Exception as e:
        csv_path = None
        print(f"Error during scraping: {e}")
    driver.quit()
    return csv_path

def data_overview_tab():
    st.header("FantasyPros Scrape Attempt")

    qb_projections_url = "https://www.fantasypros.com/nfl/projections/qb.php?week=draft"
    rb_projections_url = "https://www.fantasypros.com/nfl/projections/rb.php?week=draft"
    wr_projections_url = "https://www.fantasypros.com/nfl/projections/wr.php?week=draft"
    te_projections_url = "https://www.fantasypros.com/nfl/projections/te.php?week=draft"
    k_projections_url = "https://www.fantasypros.com/nfl/projections/k.php?week=draft"
    dst_projections_url = "https://www.fantasypros.com/nfl/projections/dst.php?week=draft"

    # Scrape QB projections CSV and load into DataFrame
    if st.button("Scrape QB Projections CSV from FantasyPros"):
        csv_path = scrape_qb_projections_csv(qb_projections_url)
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
