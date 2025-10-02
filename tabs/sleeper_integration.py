import streamlit as st
import datetime
from sleeper_wrapper import League, Players
import pandas as pd
import difflib
from plotly import graph_objects as go
import plotly.express as px

@st.cache_data(ttl=24 * 3600)  # Cache for 24 hours
def get_all_players():
    return Players().get_all_players()

def get_player_info(player_id, all_players):
    return all_players.get(player_id)

def get_player_value(row, keeptradecut_df):
    player_name = " ".join([row["search_first_name"], row["search_last_name"]])

    # Player Names are in the first column of keeptradecut_df, but the name of the column is unknown
    name_column = keeptradecut_df.columns[0]
    value_column = "Value"  # Assuming the column name is "Value"

    # Lowercase comparison for better matching
    keeptradecut_df[name_column] = keeptradecut_df[name_column].str.lower()

    # Fuzzy matching using difflib
    player_name_lower = player_name.lower()
    names_list = keeptradecut_df[name_column].tolist()
    match = difflib.get_close_matches(player_name_lower, names_list, n=1, cutoff=0.8)
    if match:
        matched_row = keeptradecut_df[keeptradecut_df[name_column] == match[0]]
    else:
        matched_row = pd.DataFrame()
    if not matched_row.empty:
        return matched_row[value_column].values[0]

@st.cache_data(ttl=24 * 3600)  # Cache for 24 hours
def get_keeptradecut_dataframe(google_sheet_url, tab_name="SF"):
    # Extract the sheet ID from the URL
    sheet_id = google_sheet_url.split("/d/")[1].split("/")[0]
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={tab_name}"
    
    # Read the CSV data into a DataFrame
    df = pd.read_csv(csv_url)
    return df

def sleeper_integration_tab():
    st.header("Sleeper Integration")
    
    cols = st.columns(3)
    with cols[0]:
        sleeper_league_id = st.text_input("Enter your Sleeper League ID:", value="1180366350202068992")
    with cols[1]:
        keeptradecut_google_sheet_url = st.text_input("Enter your KeepTradeCut Google Sheet URL:", value="https://docs.google.com/spreadsheets/d/1n5aqip8iFCpltO8deiS7q9m3u_dFvKTZpwzfZXVTpgs/")
    with cols[2]:
        tab_name = st.text_input("Enter the KeepTradeCut Tab Name:", value="SF")

    keeptradecut_df = get_keeptradecut_dataframe(keeptradecut_google_sheet_url, tab_name)
    with st.expander("KeepTradeCut Data"):
        st.dataframe(keeptradecut_df)
    
    league = League(sleeper_league_id)
    users = league.get_users()
    rosters = league.get_rosters()

    all_players = get_all_players

    user_count = len(users)
    st.write(f"Number of users in the league: {user_count}")

    default_user = "sclebow"

    # Reorder users to have the default user first
    users = sorted(users, key=lambda x: x["display_name"] != default_user)

    with st.expander("League Users and Rosters"):
        tabs = st.tabs([(user["metadata"]["team_name"] + " - " + user["display_name"]) for user in users])

    user_roster_data = {}

    for i, user in enumerate(users):
        user_id = user["user_id"]
        with tabs[i]:
            # print(user_id)
            roster = next((r for r in rosters if r["owner_id"] == user_id), None)
            # print("Roster attributes:", roster.keys() if roster else "No roster found")
            players = roster["players"]
            reserve = roster["reserve"]
            starters = roster["starters"]
            taxi = roster["taxi"]

            if not players:
                players = []
            if not reserve:
                reserve = []
            if not starters:
                starters = []
            if not taxi:
                taxi = []

            # print("Players:", players)
            # print("Reserve:", reserve)
            # print("Starters:", starters)
            # print("Taxi:", taxi)

            player_ids = list(players)

            player_dicts = []
            for player_id in player_ids:
                player_info = all_players.get(player_id)
                player_dicts.append(player_info)

            player_df = pd.DataFrame(player_dicts)

            with st.expander("Full Player Data"):
                # Sort columns alphabetically
                player_df = player_df.reindex(sorted(player_df.columns), axis=1)
                st.dataframe(player_df)

            columns_to_keep = ["search_first_name", "search_last_name", "fantasy_positions", "team", "number", "age", "years_exp", "depth_chart_order"]
            player_df = player_df[columns_to_keep]

            # Get "KTC Value" column from keeptradecut_df
            player_df["KTC Value"] = player_df.apply(lambda row: get_player_value(row, keeptradecut_df), axis=1)

            # Replace NaN values in "KTC Value" column with 0
            player_df["KTC Value"] = player_df["KTC Value"].fillna(0)

            # Sort by KTC Value descending
            player_df = player_df.sort_values(by="KTC Value", ascending=False)

            st.dataframe(player_df)

            total_ktc_value = player_df["KTC Value"].sum()
            st.write(f"Total KTC Value for {user['display_name']}: {total_ktc_value}")

            user_roster_data[user["display_name"]] = {
                "team_name": user["metadata"]["team_name"],
                "roster": player_df,
                "total_ktc_value": total_ktc_value
            }

    # Compare rosters
    st.header("Roster Comparison")
    comparison_rows = []
    for user, data in user_roster_data.items():
        comparison_rows.append({
            "User": user,
            "Team Name": data["team_name"],
            "Total KTC Value": data["total_ktc_value"],
            "Number of Players": len(data["roster"])
        })
    comparison_df = pd.DataFrame(comparison_rows)

    # Sort by Total KTC Value descending
    comparison_df = comparison_df.sort_values(by="Total KTC Value", ascending=False)

    # Create a chart to compare total KTC values
    fig = go.Figure(data=[
        go.Bar(name="Total KTC Value", x=comparison_df["User"], y=comparison_df["Total KTC Value"])
    ])
    fig.update_layout(barmode='group', title="Roster Comparison", yaxis_title="KeepTradeCut Total Roster Value")

    # Use a continuous colorscale for the bars
    colorscale = px.colors.sequential.Viridis
    fig.update_traces(marker=dict(
        color=comparison_df["Total KTC Value"],
        colorscale=colorscale,
        showscale=True
    ))

    st.plotly_chart(fig, use_container_width=True)
    with st.expander("Comparison Data"):
        st.dataframe(comparison_df)