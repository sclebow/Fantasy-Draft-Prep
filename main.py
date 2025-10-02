# This is a streamlit app that helps users prepare for their fantasy football drafts.
# It uses Fantasy Pros Projections CSV data to provide insights and recommendations.

import streamlit as st

from tabs import live_draft, data_overview, free_agents_espn, sleeper_integration

print("\n" * 10)

# STREAMLIT UI
st.set_page_config(page_title="Fantasy Football Draft Prep", layout="wide")

main_tabs = st.tabs(["Live Draft", "Data Overview", "Free Agents in ESPN", "Sleeper Integration"])
with main_tabs[1]:
    data_overview.data_overview_tab()

with main_tabs[0]:
    live_draft.live_draft_tab()

with main_tabs[2]:
    free_agents_espn.free_agents_espn_tab()

with main_tabs[3]:
    sleeper_integration.sleeper_integration_tab()