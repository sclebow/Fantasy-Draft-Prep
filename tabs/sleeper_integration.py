import streamlit as st
import datetime
from sleeper_wrapper import League, Players
import pandas as pd
import difflib
from plotly import graph_objects as go
import plotly.express as px

from scraper.ktc_to_csv import scrape_ktc

@st.cache_data(ttl=24 * 3600)  # Cache for 24 hours
def get_all_players():
    return Players().get_all_players()

def get_player_info(player_id, all_players):
    return all_players.get(player_id)

def get_player_value(row, keeptradecut_df, fuzzy_match=True):
    # print(f"Getting value for player_id: {row['player_id']}, name: {row['search_first_name']} {row['search_last_name']}")
    player_name = " ".join([row["search_first_name"], row["search_last_name"]])

    # Player Names are in the first column of keeptradecut_df, but the name of the column is unknown
    name_column = keeptradecut_df.columns[0]
    value_column = "SFValue"  # Assuming the column name is "Value"

    # Lowercase comparison for better matching
    keeptradecut_df[name_column] = keeptradecut_df[name_column].str.lower()

    if fuzzy_match:
        # Fuzzy matching using difflib
        player_name_lower = player_name.lower()
        names_list = keeptradecut_df[name_column].tolist()
        match = difflib.get_close_matches(player_name_lower, names_list, n=1, cutoff=0.9)
        if match:
            matched_row = keeptradecut_df[keeptradecut_df[name_column] == match[0]]
        else:
            matched_row = pd.DataFrame()
        if not matched_row.empty:
            return matched_row[value_column].values[0]
        
    else:
        matched_row = keeptradecut_df[keeptradecut_df[name_column] == player_name.lower()]
        if not matched_row.empty:
            return matched_row[value_column].values[0]

@st.cache_data(ttl=24 * 3600)  # Cache for 24 hours
def get_keeptradecut_dataframe():
    ktc_data = scrape_ktc()
    df = pd.DataFrame(ktc_data)

    return df

def sleeper_integration_tab():
    st.header("Sleeper Integration")
    
    cols = st.columns(3)
    with cols[0]:
        sleeper_league_id = st.text_input("Enter your Sleeper League ID:", value="1180366350202068992")

    keeptradecut_df = get_keeptradecut_dataframe()
    with st.expander("KeepTradeCut Data"):
        st.dataframe(keeptradecut_df)
    
    league = League(sleeper_league_id)
    users = league.get_users()
    rosters = league.get_rosters()

    all_players = get_all_players()

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

            columns_to_keep = ["player_id", "search_first_name", "search_last_name", "fantasy_positions", "team", "number", "age", "years_exp", "depth_chart_order"]
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

    # Find highest value KTC players that are not on any roster
    all_drafted_player_ids = []
    for data in user_roster_data.values():
        all_drafted_player_ids.extend(data["roster"]["player_id"].tolist())
    all_drafted_player_ids = set(all_drafted_player_ids)

    all_player_ids = set(all_players.keys())
    undrafted_player_ids = all_player_ids - all_drafted_player_ids

    undrafted_player_dicts = []
    for player_id in undrafted_player_ids:
        player_info = all_players.get(player_id)
        undrafted_player_dicts.append(player_info)
    undrafted_player_df = pd.DataFrame(undrafted_player_dicts)
    undrafted_player_df = undrafted_player_df[columns_to_keep]

    # Drop rows with missing first or last name
    undrafted_player_df = undrafted_player_df.dropna(subset=["search_first_name", "search_last_name"])

    # Drop rows where team is None
    undrafted_player_df.dropna(subset=["team"], inplace=True)

    # Drop rows where depth_chart_order is NaN
    undrafted_player_df.dropna(subset=["depth_chart_order"], inplace=True)

    undrafted_player_df["KTC Value"] = undrafted_player_df.apply(lambda row: get_player_value(row, keeptradecut_df, fuzzy_match=False), axis=1)
    undrafted_player_df["KTC Value"] = undrafted_player_df["KTC Value"].fillna(0)
    undrafted_player_df = undrafted_player_df.sort_values(by="KTC Value", ascending=False)

    st.header("Top Undrafted Players by KTC Value")
    st.dataframe(undrafted_player_df.head(20))
    with st.expander("All Undrafted Players"):
        st.dataframe(undrafted_player_df)

    traded_picks = league.get_traded_picks()
    standings = league.get_standings(rosters, users)

    # standings: List of tuples (team_name, wins, losses, points_for, ...)
    sorted_standings = sorted(
        standings,
        key=lambda x: (x[1], x[3]),  # x[1]=wins, x[3]=points_for
        reverse=True
    )

    st.header("Overall League Standings")
    standings_df = pd.DataFrame(sorted_standings, columns=["Team Name", "Wins", "Losses", "Points For"])
    st.dataframe(standings_df)

    st.header("Team Draft Picks")

    # st.write(traded_picks)

    # Create a dataframe for all draft picks
    # There are five rounds in the draft, and each team has one pick per round
    # In each round, the pick order is determined by the reverse order of the standings
    # We can track picks for each of the next three years
    # We typically draft in mid April, so we can assume the draft year is the current year if before April, otherwise next year
    current_year = datetime.datetime.now().year
    if datetime.datetime.now().month < 4:
        draft_year = current_year
    else:
        draft_year = current_year + 1

    draft_order = []
    for year in range(draft_year, draft_year + 4):
        for round_num in range(1, 6):
            for team in sorted_standings[::-1]:  # Reverse order of standings
                team_name = team[0]
                draft_order.append({
                    "year": year,
                    "round": round_num,
                    "pick_in_round": sorted_standings[::-1].index(team) + 1,
                    "overall_pick": (round_num - 1) * len(users) + sorted_standings[::-1].index(team) + 1,
                    "owner_team_name": team_name,
                    "previous_owner_team_name": None,
                    "owner_id": next((u["user_id"] for u in users if u["metadata"]["team_name"] == team_name), None),
                    "previous_owner_id": next((u["user_id"] for u in users if u["metadata"]["team_name"] == team_name), None),
                    "is_traded": False
                })
    draft_order_df = pd.DataFrame(draft_order)

    rosters = league.get_rosters()

    # Mark traded picks
    for pick in traded_picks:
        round_num = pick["round"]
        owner_id = pick["owner_id"]
        previous_owner_id = pick["previous_owner_id"]

        # Find the corresponding roster in rosters
        owner_roster = next((r for r in rosters if r["roster_id"] == owner_id))
        owner_id = owner_roster["owner_id"]
        previous_owner_roster = next((r for r in rosters if r["roster_id"] == previous_owner_id))
        previous_owner_id = previous_owner_roster["owner_id"]

        # Find the pick in draft_order_df and update it
        pick_index = draft_order_df[(draft_order_df["round"] == round_num) & (draft_order_df["owner_id"] == previous_owner_id)].index
        if not pick_index.empty:
            draft_order_df.at[pick_index[0], "owner_id"] = owner_id
            draft_order_df.at[pick_index[0], "owner_team_name"] = next((u["metadata"]["team_name"] for u in users if u["user_id"] == owner_id), None)
            draft_order_df.at[pick_index[0], "previous_owner_id"] = previous_owner_id
            draft_order_df.at[pick_index[0], "previous_owner_team_name"] = next((u["metadata"]["team_name"] for u in users if u["user_id"] == previous_owner_id), None)
            draft_order_df.at[pick_index[0], "is_traded"] = True

    st.dataframe(draft_order_df)

    tabs = st.tabs([team["metadata"]["team_name"] for team in users])
    for i, team in enumerate(users):
        with tabs[i]:
            team_name = team["metadata"]["team_name"]

            # Get the ranking of the team
            team_ranking = next((idx + 1 for idx, s in enumerate(sorted_standings) if s[0] == team_name), None)
            st.write(f"Team Ranking: {team_ranking}")

            # Use the draft_order_df to show the picks for this team, and use KTC Value to sort the picks
            # Picks in the early 25% of a round are "Early", the middle 50% are "Mid", and the last 25% are "Late"
            # For example, in a 10 team league, picks 1-2 are "Early", picks 3-7 are "Mid", and picks 8-10 are "Late"
            # This is important because the KTC data would list "2027 Early 1st" as a different player than "2027 Mid 1st" or "2027 Late 1st"
            team_picks = draft_order_df[draft_order_df["owner_team_name"] == team_name].copy()
            team_picks["pick_position"] = team_picks.apply(lambda row:
                "Early" if row["pick_in_round"] <= (len(users) * 0.25) else
                ("Late" if row["pick_in_round"] > (len(users) * 0.75) else "Mid"), axis=1)
            def get_ordinal_suffix(n):
                if 10 <= n % 100 <= 20:
                    suffix = "th"
                else:
                    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
                return suffix

            team_picks["KTC Pick Name"] = team_picks.apply(
                lambda row: f"{row['year']} {row['pick_position']} {row['round']}{get_ordinal_suffix(row['round'])}", 
                axis=1
            )
            # TODO: Value is coming back as 0 for all picks, need to debug
            # Look up the pick values directly in the KTC dataframe
            name_column = keeptradecut_df.columns[0]  # First column contains player/pick names
            value_column = "SFValue"  # Assuming the column name for values
            
            # Create a function to find pick values
            def find_pick_value(pick_name):
                # Look for exact match in the keeptradecut dataframe
                matched_row = keeptradecut_df[keeptradecut_df[name_column] == pick_name]
                if not matched_row.empty:
                    return matched_row[value_column].values[0]
                return 0
            
            # Apply the function to get KTC values for picks
            team_picks["KTC Value"] = team_picks["KTC Pick Name"].apply(find_pick_value)
            team_picks["KTC Value"] = team_picks["KTC Value"].fillna(0)
            team_picks = team_picks.sort_values(by="KTC Value", ascending=False)
            st.dataframe(team_picks)