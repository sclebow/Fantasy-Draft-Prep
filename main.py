# This is a streamlit app that helps users prepare for their fantasy football drafts.
# It uses Fantasy Pros Projections CSV data to provide insights and recommendations.

import streamlit as st

from utils.fantasy_pros_combined_data import create_combined_data
from scraper.fantasypros_scraper import update_session_state_with_scraped_data

st.session_state["DEFAULT_TIMEZONE"] = "US/Eastern"

st.session_state["TEAM_COLOR_MAP"] = {
    "ARI": "#97233F",
    "ATL": "#A71930",
    "BAL": "#241773",
    "BUF": "#00338D",
    "CAR": "#0085CA",
    "CHI": "#0B162A",
    "CIN": "#FB4F14",
    "CLE": "#311D00",
    "DAL": "#003594",
    "DEN": "#002244",
    "DET": "#0076B6",
    "GB": "#203731",
    "HOU": "#03202F",
    "IND": "#002C5F",
    "JAX": "#006778",
    "KC": "#E31837",
    "LAC": "#002A5E",
    "LAR": "#003594",
    "LV": "#000000",
    "MIA": "#008E97",
    "MIN": "#4F2683",
    "NE": "#002244",
    "NO": "#D3BC8D",
    "NYG": "#0B2265",
    "NYJ": "#125740",
    "PHI": "#004C54",
    "PIT": "#FFB612",
    "SF": "#AA0000",
    "SEA": "#002244",
    "TB": "#D50A0A",
    "TEN": "#4B92DB",
    "WAS": "#5A1414"
}

st.session_state["SLEEPER_LEAGUE_ID"] = "1180366350202068992"

print("\n" * 10)
print("Starting Fantasy Football Draft Prep App")

update_session_state_with_scraped_data()
create_combined_data()

st.set_page_config(page_title="Fantasy Football Draft Prep", layout="wide")
st.title("Welcome to Fantasy Football Draft Prep!")
st.write("Use the sidebar to navigate between pages.")

free_agents_page = st.Page("pages/espn/free_agents_espn.py", title="Free Agents in ESPN")
data_overview_page = st.Page("pages/espn/data_overview.py", title="Data Overview")
live_draft_page = st.Page("pages/espn/live_draft.py", title="Live Draft")

sleeper_integration_page = st.Page("pages/sleeper/sleeper_integration.py", title="Sleeper Integration")

pg = st.navigation(
    {
        "ESPN Integration": [
            free_agents_page,
            data_overview_page,
            live_draft_page
        ],
        "Sleeper Integration": [
            sleeper_integration_page
        ]
    }
)

pg.run()

# st.switch_page(sleeper_integration_page)