# This is a streamlit app that helps users prepare for their fantasy football drafts.
# It uses Fantasy Pros Projections CSV data to provide insights and recommendations.

import streamlit as st

from utils.fantasy_pros_combined_data import create_combined_data

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