# This is a streamlit app that helps users prepare for their fantasy football drafts.
# It uses Fantasy Pros Projections CSV data to provide insights and recommendations.

import streamlit as st
import pandas as pd
import numpy as np

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

# Load data
dst_data = pd.read_csv("./data_tables/FantasyPros_Fantasy_Football_Projections_DST.csv")
flx_data = pd.read_csv("./data_tables/FantasyPros_Fantasy_Football_Projections_FLX.csv")
k_data = pd.read_csv("./data_tables/FantasyPros_Fantasy_Football_Projections_K.csv")
qb_data = pd.read_csv("./data_tables/FantasyPros_Fantasy_Football_Projections_QB.csv")
adp_data = pd.read_csv("./data_tables/FantasyPros_2025_Overall_ADP_Rankings.csv", on_bad_lines='skip')

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

# Drop players with 0 points
dst_data = dst_data[dst_data["FPTS"] > 0]
flx_data = flx_data[flx_data["FPTS"] > 0]
k_data = k_data[k_data["FPTS"] > 0]
qb_data = qb_data[qb_data["FPTS"] > 0]

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

# STREAMLIT UI
st.set_page_config(page_title="Fantasy Football Draft Prep", layout="wide")

main_tabs = st.tabs(["Data Overview", "Live Draft"])
with main_tabs[0]:
    data_tabs = st.tabs(["DST", "FLX", "K", "QB", "ADP"])

    with data_tabs[0]:
        st.header("DST Input Data")
        st.dataframe(dst_data)

    with data_tabs[1]:
        st.header("FLX Input Data")
        st.dataframe(flx_data)

    with data_tabs[2]:
        st.header("K Input Data")
        st.dataframe(k_data)

    with data_tabs[3]:
        st.header("QB Input Data")
        st.dataframe(qb_data)

    with data_tabs[4]:
        st.header("ADP Input Data")
        st.dataframe(adp_data)


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

with main_tabs[1]:

    st.header("Live Draft")
    st.write("This is where we track the live draft.")

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
            hide_index=True
        )

    with cols[1]:
        st.subheader("VOBP")
        st.dataframe(
            vobb_df.sort_values(by="VOBP", ascending=False).style.apply(highlight_drafted, axis=1),
            hide_index=True
        )