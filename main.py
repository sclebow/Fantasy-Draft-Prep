# This is a streamlit app that helps users prepare for their fantasy football drafts.
# It uses Fantasy Pros Projections CSV data to provide insights and recommendations.

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from espn_api import football

print("\n" * 10)

SCORING_MULTIPLIER_DICT = {
    "PY": 0.04,
    "PTD": 4,
    "INT": -2,
    "2PC": 2,
    "RY": 0.01,
    "RTD": 6,
    "2PR": 2,
    "REY": 0.1,
    "REC": 0.5,
    "2PRE": 2,
    "PAT": 1,
    "FGM": -1,
    "FG0": 3,
    "FG40": 4,
    "FG50": 5,
    "FG60": 5
}

ROSTER_SPOTS_PER_POSITION_DICT = {
    "QB": {
        "starters": 1,
        "max": 4,
        "likely_benched": 2
    },
    "RB": {
        "starters": 2,
        "max": 8,
        "likely_benched": 2
    },
    "WR": {
        "starters": 2,
        "max": 8,
        "likely_benched": 2
    },
    "TE": {
        "starters": 1,
        "max": 3,
        "likely_benched": 1
    },
    "K": {
        "starters": 1,
        "max": 3,
        "likely_benched": 0
    },
    "DST": {
        "starters": 1,
        "max": 3,
        "likely_benched": 0
    }
}

NUMBER_OF_TEAMS = 10

HEAD_COUNT = 5

# Load data
st.session_state["dst_data"] = pd.read_csv("./data_tables/FantasyPros_Fantasy_Football_Projections_DST.csv")
st.session_state["flx_data"] = pd.read_csv("./data_tables/FantasyPros_Fantasy_Football_Projections_FLX.csv")
st.session_state["k_data"] = pd.read_csv("./data_tables/FantasyPros_Fantasy_Football_Projections_K.csv")
st.session_state["qb_data"] = pd.read_csv("./data_tables/FantasyPros_Fantasy_Football_Projections_QB.csv")
st.session_state["adp_data"] = pd.read_csv("./data_tables/FantasyPros_2025_Overall_ADP_Rankings.csv", on_bad_lines='skip')

def process_combined_data(dst_data, flx_data, k_data, qb_data, adp_data):
    def process_data(df):
        # Basic data cleaning and preprocessing
        df = df.dropna()
        return df

    dst_data["POS"] = "DST"
    dst_data.drop(columns=["Team"], inplace=True)

    k_data["POS"] = "K"

    qb_data["POS"] = "QB"

    dst_data = process_data(dst_data)
    flx_data = process_data(flx_data)
    k_data = process_data(k_data)
    qb_data = process_data(qb_data)

    # Process FLX columns
    column_rename_dict = {
        "YDS": "RY",
        "TDS": "TRD",
        "YDS.1": "REY",
        "TDS.1": "RETD",
        "FL": "FUML"
    }

    flx_data = flx_data.rename(columns=column_rename_dict)

    # Drop columns not in column_rename_dict
    flx_data = flx_data[["Player", "Team", "POS", "RY", "TRD", "REY", "RETD", "FUML"]]

    # Remove ',' from numeric columns
    flx_data[["RY", "TRD", "REY", "RETD", "FUML"]] = flx_data[["RY", "TRD", "REY", "RETD", "FUML"]].replace(',', '', regex=True)

    # Convert all relevant columns to numeric
    flx_data[["RY", "TRD", "REY", "RETD", "FUML"]] = flx_data[["RY", "TRD", "REY", "RETD", "FUML"]].apply(pd.to_numeric, errors='coerce')

    # Replace NaN values with 0
    flx_data.fillna(0, inplace=True)

    # Keep only first two characters of the POS
    flx_data["POS"] = flx_data["POS"].str[:2]

    # Calculate fantasy points
    def calculate_fantasy_points(row):
        points = 0
        for col in flx_data.columns[1:]:
            if col in SCORING_MULTIPLIER_DICT:
                # print(f"Calculating points for {col}: {row[col]} * {SCORING_MULTIPLIER_DICT[col]}")
                points += row[col] * SCORING_MULTIPLIER_DICT.get(col)
        return points

    flx_data["FPTS"] = flx_data.apply(calculate_fantasy_points, axis=1)

    # Set Position of players not in the ROSTER_SPOTS_PER_POSITION_DICT to "RB"
    flx_data.loc[~flx_data["POS"].isin(ROSTER_SPOTS_PER_POSITION_DICT.keys()), "POS"] = "RB"

    # Process QB Columns
    column_rename_dict = {
        "YDS": "PY",
        "TDS": "PTD",
        "INTS": "INT",
        "YDS.1": "RY",
        "TDS.1": "RTD",
        "FL": "FUML"
    }

    qb_data = qb_data.rename(columns=column_rename_dict)

    # Drop columns not in column_rename_dict
    qb_data = qb_data[["Player", "Team", "POS", "PY", "PTD", "INT", "RY", "RTD", "FUML"]]

    # Remove ',' from numeric columns
    qb_data[["PY", "PTD", "INT", "RY", "RTD", "FUML"]] = qb_data[["PY", "PTD", "INT", "RY", "RTD", "FUML"]].replace(',', '', regex=True)

    # Convert all relevant columns to numeric
    qb_data[["PY", "PTD", "INT", "RY", "RTD", "FUML"]] = qb_data[["PY", "PTD", "INT", "RY", "RTD", "FUML"]].apply(pd.to_numeric, errors='coerce')

    # Replace NaN values with 0
    qb_data.fillna(0, inplace=True)

    # Calculate fantasy points
    def calculate_fantasy_points(row):
        points = 0
        for col in qb_data.columns[1:]:
            if col in SCORING_MULTIPLIER_DICT:
                # print(f"Calculating points for {col}: {row[col]} * {SCORING_MULTIPLIER_DICT[col]}")
                points += row[col] * SCORING_MULTIPLIER_DICT.get(col)
        return points

    qb_data["FPTS"] = qb_data.apply(calculate_fantasy_points, axis=1)

    # # Drop players with 0 points
    # dst_data = dst_data[dst_data["FPTS"] > 0]
    # flx_data = flx_data[flx_data["FPTS"] > 0]
    # k_data = k_data[k_data["FPTS"] > 0]
    # qb_data = qb_data[qb_data["FPTS"] > 0]

    # Calculate position rankings for all tables
    def calculate_position_rankings(df):
        df = df.copy()

        unique_positions = df["POS"].unique()
        df_pos_list = []
        for pos in unique_positions:
            df_pos = df[df["POS"] == pos].copy()
            df_pos["FPTS_Rank"] = df_pos["FPTS"].rank(ascending=False)
            df_pos_list.append(df_pos)

        return pd.concat(df_pos_list, ignore_index=True)

    def calculate_vorp(df, ROSTER_SPOTS_PER_POSITION_DICT, NUMBER_OF_TEAMS):
        positions = df["POS"].unique().tolist()
        # print(f"Processing positions: {positions}")
        table_dfs = []
        for table_position in positions:
            # print(f"Processing position: {table_position}")
            df_position = df[df["POS"] == table_position].copy()
            starter_count = ROSTER_SPOTS_PER_POSITION_DICT.get(table_position).get("starters")
            likely_on_bench = ROSTER_SPOTS_PER_POSITION_DICT.get(table_position).get("likely_benched")
            available_spots = starter_count + likely_on_bench
            # print(f"Available spots for {table_position}: {available_spots}")

            total_players_on_rosters_in_league = available_spots * NUMBER_OF_TEAMS

            df_position["Waiver"] = df_position["FPTS_Rank"] > total_players_on_rosters_in_league

            waiver_players = df_position[df_position["Waiver"]]
            max_fpts = waiver_players["FPTS"].max() if not waiver_players.empty else 0

            df_position["VORP"] = df_position["FPTS"] - max_fpts

            table_dfs.append(df_position)

        return pd.concat(table_dfs, ignore_index=True)

    # Combine all data, only keeping "Player", "Team", "POS", and "FPTS"
    combined_data = pd.concat([dst_data, flx_data, k_data, qb_data], ignore_index=True)

    combined_data = calculate_position_rankings(combined_data)
    combined_data = calculate_vorp(combined_data, ROSTER_SPOTS_PER_POSITION_DICT, NUMBER_OF_TEAMS)

    def calculate_vobp(df, ROSTER_SPOTS_PER_POSITION_DICT, NUMBER_OF_TEAMS):
        positions = df["POS"].unique().tolist()
        # print(f"Processing positions: {positions}")
        table_dfs = []
        for table_position in positions:
            # print(f"Processing position: {table_position}")
            df_position = df[df["POS"] == table_position].copy()
            starter_count = ROSTER_SPOTS_PER_POSITION_DICT.get(table_position).get("starters")
            available_spots = starter_count
            # print(f"Available spots for {table_position}: {available_spots}")

            total_players_on_rosters_in_league = available_spots * NUMBER_OF_TEAMS

            df_position["Bench"] = df_position["FPTS_Rank"] > total_players_on_rosters_in_league

            waiver_players = df_position[df_position["Bench"]]
            max_fpts = waiver_players["FPTS"].max() if not waiver_players.empty else 0

            df_position["VOBP"] = df_position["FPTS"] - max_fpts

            table_dfs.append(df_position)

        return pd.concat(table_dfs, ignore_index=True)

    combined_data = calculate_vobp(combined_data, ROSTER_SPOTS_PER_POSITION_DICT, NUMBER_OF_TEAMS)

    combined_data = combined_data[["Player", "POS", "FPTS_Rank", "FPTS", "VORP", "VOBP"]]

    # Merge ADP data
    combined_data = combined_data.merge(adp_data[["Player", "AVG"]], on="Player", how="left")

    # Rename columns for clarity
    combined_data = combined_data.rename(columns={"AVG": "ADP"})

    # Replace NaN values with inf
    combined_data = combined_data.replace({np.nan: float("inf")})

    # Add Drafted column (default False)
    combined_data["Drafted"] = False

    def calculate_value_against_adp(df):
        df["VORP_Rank"] = df["VORP"].rank(ascending=False)
        df["VOBP_Rank"] = df["VOBP"].rank(ascending=False)
        df["VORP_Value_Against_ADP"] = df["VORP"] - df["ADP"]
        df["VOBP_Value_Against_ADP"] = df["VOBP"] - df["ADP"]
        return df

    combined_data = calculate_value_against_adp(combined_data)

    return combined_data

# STREAMLIT UI
st.set_page_config(page_title="Fantasy Football Draft Prep", layout="wide")

main_tabs = st.tabs(["Live Draft", "Data Overview", "Free Agents in ESPN"])
with main_tabs[1]:
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

    combined_data = process_combined_data(
        dst_data=st.session_state["dst_data"],
        flx_data=st.session_state["flx_data"],
        k_data=st.session_state["k_data"],
        qb_data=st.session_state["qb_data"],
        adp_data=st.session_state["adp_data"]
    )

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

with main_tabs[0]:

    st.header("Live Draft")

    combined_data.sort_values(by="ADP", inplace=True)

    # Multiselect for drafted players
    drafted_players = st.multiselect(
        "Mark players as drafted:",
        options=combined_data["Player"].tolist(),
        default=[]
    )
    # Mark drafted players in the DataFrame
    combined_data["Drafted"] = combined_data["Player"].isin(drafted_players)

    vorp_df = combined_data[["Player", "POS", "VORP", "VORP_Rank", "VORP_Value_Against_ADP", "Drafted"]]
    vobb_df = combined_data[["Player", "POS", "VOBP", "VOBP_Rank", "VOBP_Value_Against_ADP", "Drafted"]]

    # Highlight drafted players in yellow
    def highlight_drafted(row):
        color = "background-color: yellow" if row["Drafted"] else ""
        return [color] * len(row)

    cols = st.columns(2)
    with cols[0]:
        st.subheader("VORP")
        st.dataframe(
            vorp_df.sort_values(by="VORP", ascending=False).style.apply(highlight_drafted, axis=1),
            hide_index=True,
            height=200
        )

    with cols[1]:
        st.subheader("VOBP")
        st.dataframe(
            vobb_df.sort_values(by="VOBP", ascending=False).style.apply(highlight_drafted, axis=1),
            hide_index=True,
            height=200
        )

    cols = st.columns(3)
    
    with cols[0]:
        st.markdown(f"### Top {HEAD_COUNT} ADP Available")
        top_adp = combined_data[~combined_data["Drafted"]].sort_values(by="ADP", ascending=True).head(HEAD_COUNT)
        top_adp = top_adp[["Player", "POS", "ADP"]]
        st.dataframe(
            top_adp,
            hide_index=True
        )

    with cols[1]:
        st.markdown(f"### Top {HEAD_COUNT} VORP Available")
        top_vorp = vorp_df[~vorp_df["Drafted"]].sort_values(by="VORP", ascending=False).head(HEAD_COUNT)
        top_vorp = top_vorp[["Player", "POS", "VORP"]]
        st.dataframe(
            top_vorp,
            hide_index=True
        )

    with cols[2]:
        st.markdown(f"### Top {HEAD_COUNT} VOBP Available")
        top_vobb = vobb_df[~vobb_df["Drafted"]].sort_values(by="VOBP", ascending=False).head(HEAD_COUNT)
        top_vobb = top_vobb[["Player", "POS", "VOBP"]]
        st.dataframe(
            top_vobb,
            hide_index=True
        )

    st.markdown("### Top Players by combined Top Metrics")
    columns = ["Player", "In Top ADP", "In Top VORP", "In Top VOBP"]
    combined_top_metrics = {
        "Player": [],
        "In Top ADP": [],
        "In Top VORP": [],
        "In Top VOBP": []
    }

    for player in top_adp["Player"]:
        combined_top_metrics["Player"].append(player)
        combined_top_metrics["In Top ADP"].append(player in top_adp["Player"].values)
        combined_top_metrics["In Top VORP"].append(player in top_vorp["Player"].values)
        combined_top_metrics["In Top VOBP"].append(player in top_vobb["Player"].values)

    combined_top_metrics = pd.DataFrame(combined_top_metrics)
    combined_top_metrics["Count"] = combined_top_metrics[["In Top ADP", "In Top VORP", "In Top VOBP"]].sum(axis=1)
    combined_top_metrics = combined_top_metrics[["Player", "Count"]].sort_values(by="Count", ascending=False).head(10)

    top_players = combined_top_metrics["Player"].values.tolist()

    st.markdown(", ".join([f"{player}" for player in top_players]))

with main_tabs[2]:
    st.header("Free Agents in your ESPN League")

    cols = st.columns(2)
    with cols[0]:
        st.session_state["espn_league_id"] = st.number_input("Enter your ESPN League ID:", value=1462856)
    with cols[1]:
        st.session_state["espn_year"] = st.number_input("Enter your ESPN Year:", value=datetime.now().year)

    @st.cache_data
    def get_league():
        return football.League(st.session_state["espn_league_id"], st.session_state["espn_year"])

    st.markdown("---")

    st.subheader("Top Free Agents For Full Season using FantasyPros Projections")
    league = get_league()
    free_agents = list(league.free_agents(size=1000))
    free_agent_names = []
    for player in free_agents:
        free_agent_names.append(player.__getattribute__("name"))
    
    free_agent_df = pd.DataFrame({"Player": free_agent_names})

    # Remove " D/ST"
    free_agent_df["Player"] = free_agent_df["Player"].str.replace(" D/ST", "", regex=False)

    # Merge with combined data
    merged_df = pd.merge(free_agent_df, combined_data, on="Player", how="left")
    merged_df = merged_df.fillna({
        "POS": "DST",
    })

    dst_data = merged_df[merged_df["POS"] == "DST"]

    # Try to fuzzy match DST players with combined data, the issue is that in the Combined Data a Team will be called "San Francisco 49ers", but in the Free Agents it will be "49ers"
    def fuzzy_match_dst_players(dst_data, combined_data):
        dst_teams = dst_data["Player"].values
        combined_players = combined_data["Player"].values
        matched_teams = []
        for dst_team in dst_teams:
            # Fuzzy match the team 
            matched = None
            for combined_player in combined_players:
                if dst_team in combined_player and dst_team != combined_player:
                    matched = combined_player
                    break
            matched_teams.append(matched)
        return matched_teams

    dst_data["Player"] = fuzzy_match_dst_players(dst_data, combined_data)
    dst_data = dst_data.dropna(subset=["Player"])
    dst_data = dst_data[["Player", "POS"]]
    dst_data = pd.merge(dst_data, combined_data, on=["Player", "POS"], how="left")
    dst_data = dst_data.dropna(subset=["FPTS"])

    merged_df = pd.concat([merged_df[merged_df["POS"] != "DST"], dst_data], ignore_index=True)
    merged_df.sort_values(by=["FPTS"], ascending=False, inplace=True)

    st.dataframe(merged_df, hide_index=True)

    st.markdown("---")

    st.subheader("Top Free Agents For Week by Projected Points using ESPN Projections")

    cols = st.columns(2)
    with cols[0]:
        week_number = st.number_input("Enter the week number:", value=league.current_week)

    free_agents_week = list(league.free_agents(size=1000, week=week_number))

    with cols[1]:
        st.markdown(f"Current Week: {league.current_week}")

    player_dict = {}
    for player in free_agents_week:
        attributes = player.__dict__
        player_dict[player.name] = attributes

    free_agents_week_df = pd.DataFrame.from_dict(player_dict, orient="index")
    free_agents_week_df = free_agents_week_df[["name", "projected_points", "position", "posRank", "proTeam", "injuryStatus", "percent_owned"]]
    free_agents_week_df["Count by Position"] = free_agents_week_df["position"].map(free_agents_week_df["position"].value_counts())
    free_agents_week_df = free_agents_week_df[free_agents_week_df["Count by Position"] >= 2]

    free_agents_week_df.sort_values("projected_points", ascending=False, inplace=True)

    unique_positions = free_agents_week_df["position"].unique()

    cols = st.columns(len(unique_positions))

    for col, pos in zip(cols, unique_positions):
        with col:
            st.subheader(pos)
            st.dataframe(free_agents_week_df[free_agents_week_df["position"] == pos], hide_index=True)
            st.write(f"Most Projected Points: {free_agents_week_df[free_agents_week_df['position'] == pos]['projected_points'].max()}")