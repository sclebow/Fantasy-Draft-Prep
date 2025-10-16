import streamlit as st
import datetime
from sleeper_wrapper import League, Players
import pandas as pd
import requests
import difflib

from plotly import graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from scraper.ktc_to_csv import scrape_ktc

TEAM_COLOR_MAP = {
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

pd.set_option('future.no_silent_downcasting', True)

@st.cache_data(ttl=24 * 3600)  # Cache for 24 hours
def get_all_players():
    return Players().get_all_players()

def get_player_info(player_id, all_players):
    return all_players.get(player_id)

def get_player_value(row, keeptradecut_df, fuzzy_match=True):
    # print(f"Getting value for player_id: {row['player_id']}, name: {row['search_first_name']} {row['search_last_name']}")
    player_full_name = " ".join([row["search_first_name"], row["search_last_name"]])
    player_last_name = row["search_last_name"]
    player_first_name = row["search_first_name"]
    player_team = row["team"]

    if player_team == "JAX":
        player_team = "JAC"  # KTC uses JAC for Jacksonville

    # Player Names are in the first column of keeptradecut_df, but the name of the column is unknown
    ktc_name_column = keeptradecut_df.columns[0]
    ktc_value_column = "SFValue"  # Assuming the column name is "Value"
    ktc_team_column = "Team"

    # Clean up player names in keeptradecut_df by stripping periods
    keeptradecut_df[ktc_name_column] = keeptradecut_df[ktc_name_column].str.replace('.', '', regex=False).str.strip()

    # Check for rows that contain the player's last name (case insensitive)
    matched_row = keeptradecut_df[keeptradecut_df[ktc_name_column].str.contains(player_last_name, case=False, na=False)]

    # Further filter by first name
    matched_row = matched_row[matched_row[ktc_name_column].str.contains(player_first_name, case=False, na=False)]

    # Check to make sure the player's first name comes before the last name in the matched rows
    matched_row = matched_row[matched_row[ktc_name_column].str.lower().str.index(player_first_name.lower()) < matched_row[ktc_name_column].str.lower().str.index(player_last_name.lower())]

    # Check that the team matches using the ktc_team_column
    # The ktc data uses three letter team abbreviations, but sleeper uses two or three letter abbreviations, depending on the team
    # For example, "New England Patriots" is "NE" in sleeper but "NEP" in ktc
    # If the player's team is None, skip this filtering step
    if player_team:
        matched_row = matched_row[matched_row[ktc_team_column].str.contains(player_team, case=False, na=False)]

    # Return the value
    if not matched_row.empty:
        if not matched_row.empty:
            return matched_row[ktc_value_column].values[0]
        else:
            return None

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

    # Get standings and traded picks data first (needed for draft picks calculation)
    traded_picks = league.get_traded_picks()
    standings = league.get_standings(rosters, users)

    for i in range(len(standings)):
        standings[i] = list(standings[i])
        standings[i][3] = float(standings[i][3])  # Points For
        standings[i] = tuple(standings[i])

    # standings: List of tuples (team_name, wins, losses, points_for, ...)
    sorted_standings = sorted(
        standings,
        key=lambda x: (x[1], x[3]),  # x[1]=wins, x[3]=points_for
        reverse=True
    )

    st.header("Overall League Standings")
    standings_df = pd.DataFrame(sorted_standings, columns=["Team Name", "Wins", "Losses", "Points For"])
    st.dataframe(standings_df)

    default_user = "sclebow"

    # Reorder users to have the default user first
    users = sorted(users, key=lambda x: x["display_name"] != default_user)

    # Calculate draft picks for all teams (needed for roster tabs)
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

    # Add pick position and KTC names to draft picks
    draft_order_df["pick_position"] = draft_order_df.apply(lambda row:
        "Early" if row["pick_in_round"] <= (len(users) * 0.25) else
        ("Late" if row["pick_in_round"] > (len(users) * 0.75) else "Mid"), axis=1)
    
    def get_ordinal_suffix(n):
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return suffix

    draft_order_df["KTC Pick Name"] = draft_order_df.apply(
        lambda row: f"{row['year']} {row['pick_position']} {row['round']}{get_ordinal_suffix(row['round'])}", 
        axis=1
    )

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
    draft_order_df["KTC Value"] = draft_order_df["KTC Pick Name"].apply(find_pick_value)
    draft_order_df["KTC Value"] = draft_order_df["KTC Value"].fillna(0)

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

            # Get draft picks for this team
            team_name = user["metadata"]["team_name"]
            team_picks = draft_order_df[draft_order_df["owner_team_name"] == team_name].copy()
            team_picks = team_picks.sort_values(by="KTC Value", ascending=False)
            
            st.subheader("Draft Picks")
            if not team_picks.empty:
                # Display only relevant columns for draft picks
                picks_display_df = team_picks[["year", "round", "pick_in_round", "KTC Pick Name", "KTC Value", "is_traded"]].copy()
                picks_display_df = picks_display_df.rename(columns={
                    "year": "Year",
                    "round": "Round", 
                    "pick_in_round": "Pick #",
                    "KTC Pick Name": "Pick Name",
                    "KTC Value": "KTC Value",
                    "is_traded": "Traded"
                })
                st.dataframe(picks_display_df)
                picks_ktc_value = team_picks["KTC Value"].sum()
            else:
                st.write("No draft picks found for this team")
                picks_ktc_value = 0

            total_ktc_value = player_df["KTC Value"].sum() + picks_ktc_value
            st.write(f"Total Player KTC Value: {player_df['KTC Value'].sum()}")
            st.write(f"Total Draft Picks KTC Value: {picks_ktc_value}")
            st.write(f"**Total KTC Value for {user['display_name']}: {total_ktc_value}**")

            user_roster_data[user["display_name"]] = {
                "team_name": user["metadata"]["team_name"],
                "roster": player_df,
                "total_ktc_value": total_ktc_value,
                "picks_ktc_value": picks_ktc_value,
                "draft_picks": team_picks
            }

    # Compare rosters
    st.header("Roster Comparison")
    comparison_rows = []
    for user, data in user_roster_data.items():
        player_ktc_value = data["roster"]["KTC Value"].sum()
        picks_ktc_value = data.get("picks_ktc_value", 0)
        comparison_rows.append({
            "User": user,
            "Team Name": data["team_name"],
            "Player KTC Value": player_ktc_value,
            "Draft Picks KTC Value": picks_ktc_value,
            "Total KTC Value": data["total_ktc_value"],
            "Number of Players": len(data["roster"]),
            "Number of Draft Picks": len(data.get("draft_picks", []))
        })
    comparison_df = pd.DataFrame(comparison_rows)

    # Sort by Total KTC Value descending
    comparison_df = comparison_df.sort_values(by="Total KTC Value", ascending=False)

    # Create a stacked bar chart using plotly, that shows total KTC value for each user, with player value and draft pick value as different colors
    fig = go.Figure(data=[
        go.Bar(name="Player KTC Value", x=comparison_df["User"], y=comparison_df["Player KTC Value"]),
        go.Bar(name="Draft Picks KTC Value", x=comparison_df["User"], y=comparison_df["Draft Picks KTC Value"])
    ])
    fig.update_layout(barmode='stack', title="Roster Comparison", yaxis_title="KeepTradeCut Total Roster Value")

    st.plotly_chart(fig, use_container_width=True)
    with st.expander("Comparison Data"):
        st.dataframe(comparison_df)

    # Create a pie chart showing the distribution of KTC value per player for all teams
    tabs = st.tabs([user for user in user_roster_data.keys()])
    for i, user in enumerate(user_roster_data.keys()):
        with tabs[i]:
            data = user_roster_data[user]
            roster = data["roster"]
            if roster.empty:
                st.write("No players in roster")
                continue

            cols = st.columns(2)
            with cols[0]:
                # Create a sunburst chart (stacked pie) with inner layer as position, outer as player
                # Use the first fantasy position listed for each player
                roster["fantasy_positions"] = roster["fantasy_positions"].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else "N/A")
                fig = px.sunburst(
                    roster,
                    path=["fantasy_positions", "search_last_name"],
                    values="KTC Value",
                    title=f"KTC Value Distribution for {user} (Position → Player)"
                )

                # Add percentage to labels
                total_value = roster["KTC Value"].sum()
                fig.update_traces(textinfo="label+percent entry", hovertemplate='%{label}<br>KTC Value: %{value}<br>Percentage of Total: %{percentParent:.2%}<extra></extra>')                

                fig.update_layout(margin=dict(t=40, l=0, r=0, b=0))

                st.plotly_chart(fig, use_container_width=True)
            with cols[1]:
                # Create a sunburst chart (stacked pie) with inner layer as team, outer as player
                roster["team"] = roster["team"].fillna("N/A")
                fig = px.sunburst(
                    roster,
                    path=["team", "search_last_name"],
                    values="KTC Value",
                    title=f"KTC Value Distribution for {user} (Team → Player)",
                    color="team",
                    color_discrete_map=TEAM_COLOR_MAP
                )

                # Add percentage to labels
                total_value = roster["KTC Value"].sum()
                fig.update_traces(textinfo="label+percent entry", hovertemplate='%{label}<br>KTC Value: %{value}<br>Percentage of Total: %{percentParent:.2%}<extra></extra>')
                fig.update_layout(margin=dict(t=40, l=0, r=0, b=0))

                st.plotly_chart(fig, use_container_width=True)
            with st.expander("Roster Data"):
                st.dataframe(roster)

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

    # Create a calendar of upcoming NFL games with your players highlighted
    st.header("Upcoming NFL Games Calendar with Your Players")
    user_keys = list(user_roster_data.keys())
    selected_team = st.selectbox("Select Team to Show Players From:", options=user_keys, index=0)

    # Get week from Sleeper NFL State endpoint
    url = "https://api.sleeper.app/v1/state/nfl"
    response = pd.read_json(url, typ='series')
    week = response.get("week")

    st.write(f"Current NFL Week: {week}")

    # Use espn api to get NFL schedule for the week
    @st.cache_data(ttl=24 * 3600)  # Cache for 24 hours
    def get_nfl_schedule(current_year, week):
        url = f"https://cdn.espn.com/core/nfl/schedule?xhr=1&year={current_year}&week={week}"
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return data
        else: return None
    schedule_data = get_nfl_schedule(current_year, week)
    schedule_data = schedule_data["content"]["schedule"]

    player_week_dict = {}

    for date_string in schedule_data.keys():
        games = schedule_data[date_string]["games"]
        date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
        st.subheader(f"Games for {date.strftime('%A, %B %d, %Y')}")
        data = schedule_data[date_string]
        games_df = pd.DataFrame(games)

        for game in games:
            short_name = game["shortName"]
            if "@" in short_name:
                try:
                    away_team, home_team = short_name.split(" @ ")
                except ValueError:
                    st.warning(f"Could not parse game short name: {short_name}")
            elif "VS" in short_name:
                try:
                    home_team, away_team = short_name.split(" VS ")
                except ValueError:
                    st.warning(f"Could not parse game short name: {short_name}")
            elif "vs" in short_name:
                try:
                    home_team, away_team = short_name.split(" vs ")
                except ValueError:
                    st.warning(f"Could not parse game short name: {short_name}")
            elif "At" in short_name:
                try:
                    away_team, home_team = short_name.split(" At ")
                except ValueError:
                    st.warning(f"Could not parse game short name: {short_name}")
            elif "at" in short_name:
                try:
                    away_team, home_team = short_name.split(" at ")
                except ValueError:
                    st.warning(f"Could not parse game short name: {short_name}")
            else:
                st.warning(f"Could not parse game short name: {short_name}")
                continue
            
            # Show players from selected team that are on either the away or home team
            selected_team_roster = user_roster_data[selected_team]["roster"]
            players_in_game = selected_team_roster[(selected_team_roster["team"] == away_team) | (selected_team_roster["team"] == home_team)]
            if not players_in_game.empty:
                state = game["status"]["type"]["state"]
                if state == "pre":
                    status = "Scheduled"
                elif state == "in":
                    status = "In Progress"
                elif state == "post":
                    status = "Final"
                else:
                    status = state.capitalize()

                start_time = game["date"]
                start_time = datetime.datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                
                # Convert start_time to local timezone
                start_time = start_time.astimezone()
                st.write(f"**{away_team} at {home_team}** - {status} - Start Time: {start_time.strftime('%I:%M %p %Z')}")

                st.write(f"Players from {selected_team['metadata']['team_name']} in this game:")
                st.dataframe(players_in_game)

                if start_time not in player_week_dict:
                    player_week_dict[start_time] = {}
                player_week_dict[start_time][f"{away_team} at {home_team}"] = {
                    "status": status,
                    "players": players_in_game
                }
            else:
                st.write(f"No players from {selected_team['metadata']['team_name']} in this game.")

    if not player_week_dict:
        st.write(f"No players from {selected_team['metadata']['team_name']} found in any games for week {week}.")

    else:
        # Using plotly to create a timeline of games with your players highlighted
        # Y-axis is the time of day, X-axis is the day of the week
        timeline_data = []
        for game_time, game_info in player_week_dict.items():
            for game, details in game_info.items():
                for player in details["players"].to_dict(orient="records"):
                    timeline_data.append({
                        "player_full_name": " ".join([player["search_first_name"], player["search_last_name"]]),
                        "game": game,
                        "date": game_time.date(),
                        "time_of_day": game_time.time(),
                        "home_team": game.split(" at ")[1],
                        "away_team": game.split(" at ")[0],
                    })

        if timeline_data:
            timeline_df = pd.DataFrame(timeline_data)
            with st.expander("Game Timeline Data"):
                st.dataframe(timeline_df)

            # Create a game_df that counts the number of players in each game
            game_df = timeline_df.groupby("game").agg(num_players=("player_full_name", "count")).reset_index()
            game_df = game_df.merge(timeline_df[["game", "date", "time_of_day", "home_team", "away_team"]].drop_duplicates(), on="game", how="left")
            game_df = game_df.sort_values(by=["date", "time_of_day"])

            # Create a grouped bar chart using plotly, that shows the number of players in each game
            # Each bar is a datetime, with a bar for each game that day
            fig = px.bar(
                game_df,
                x="date",
                y="num_players",
                color="game",
                title="Number of Players in Each Game",
                labels={"num_players": "Number of Players", "date": "Date"},
                height=400
            )
            fig.update_layout(barmode="group")

            st.plotly_chart(fig)
