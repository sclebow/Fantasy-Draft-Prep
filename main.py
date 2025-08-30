# This is a streamlit app that helps users prepare for their fantasy football drafts.
# It uses Fantasy Pros Projections CSV data to provide insights and recommendations.

import streamlit as st
import pandas as pd

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
    df["Rank"] = df["FPTS"].rank(ascending=False)
    return df

dst_data = calculate_position_rankings(dst_data)
flx_data = calculate_position_rankings(flx_data)
k_data = calculate_position_rankings(k_data)
qb_data = calculate_position_rankings(qb_data)

def calculate_vorp(df, ROSTER_SPOTS_PER_POSITION_DICT, NUMBER_OF_TEAMS):
    positions = df["POS"].unique().tolist()
    print(f"Processing positions: {positions}")
    table_dfs = []
    for table_position in positions:
        print(f"Processing position: {table_position}")
        df_position = df[df["POS"] == table_position]
        starter_count = ROSTER_SPOTS_PER_POSITION_DICT.get(table_position).get("starters")
        likely_on_bench = ROSTER_SPOTS_PER_POSITION_DICT.get(table_position).get("likely_benched")
        available_spots = starter_count + likely_on_bench
        print(f"Available spots for {table_position}: {available_spots}")

        total_players_on_rosters_in_league = available_spots * NUMBER_OF_TEAMS

        df_position["Waiver"] = df_position["Rank"] > total_players_on_rosters_in_league

        waiver_players = df_position[df_position["Waiver"]]
        max_fpts = waiver_players["FPTS"].max() if not waiver_players.empty else 0

        df_position["VORP"] = df_position["FPTS"] - max_fpts

        table_dfs.append(df_position)

    return pd.concat(table_dfs, ignore_index=True)

# Combine all data, only keeping "Player", "Team", "POS", and "FPTS"
combined_data = pd.concat([dst_data, flx_data, k_data, qb_data], ignore_index=True)

combined_data = calculate_vorp(combined_data, ROSTER_SPOTS_PER_POSITION_DICT, NUMBER_OF_TEAMS)

def calculate_vobp(df, ROSTER_SPOTS_PER_POSITION_DICT, NUMBER_OF_TEAMS):
    positions = df["POS"].unique().tolist()
    print(f"Processing positions: {positions}")
    table_dfs = []
    for table_position in positions:
        print(f"Processing position: {table_position}")
        df_position = df[df["POS"] == table_position]
        starter_count = ROSTER_SPOTS_PER_POSITION_DICT.get(table_position).get("starters")
        available_spots = starter_count
        print(f"Available spots for {table_position}: {available_spots}")

        total_players_on_rosters_in_league = available_spots * NUMBER_OF_TEAMS

        df_position["Bench"] = df_position["Rank"] > total_players_on_rosters_in_league

        waiver_players = df_position[df_position["Bench"]]
        max_fpts = waiver_players["FPTS"].max() if not waiver_players.empty else 0

        df_position["VOBP"] = df_position["FPTS"] - max_fpts

        table_dfs.append(df_position)

    return pd.concat(table_dfs, ignore_index=True)

combined_data = calculate_vobp(combined_data, ROSTER_SPOTS_PER_POSITION_DICT, NUMBER_OF_TEAMS)

combined_data = combined_data[["Player", "Team", "POS", "FPTS", "VORP", "VOBP"]]

# STREAMLIT UI
st.set_page_config(page_title="Fantasy Football Draft Prep", layout="wide")

main_tabs = st.tabs(["Data Overview", "Live Draft"])
with main_tabs[0]:
    data_tabs = st.tabs(["DST", "FLX", "K", "QB"])

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

st.markdown("---")
st.header("Combined Player Data with Fantasy Points")
st.dataframe(combined_data)