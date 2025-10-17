import streamlit as st
import pandas as pd
from datetime import datetime
from espn_api import football

def free_agents_espn_tab():
    combined_data = st.session_state["combined_data"]

    st.header("Free Agents in your ESPN League")

    cols = st.columns(5)
    with cols[0]:
        st.session_state["espn_league_id"] = st.number_input("Enter your ESPN League ID:", value=1462856)
    with cols[1]:
        st.session_state["espn_year"] = st.number_input("Enter your ESPN Year:", value=datetime.now().year)

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_league():
        return football.League(st.session_state["espn_league_id"], st.session_state["espn_year"])
    league = get_league()

    with cols[2]:
        st.session_state["selected_team"] = st.selectbox("Select your team:", options=league.teams, index=7)

    with cols[3]:
        week_number = st.number_input("Enter the week number:", value=league.current_week)

    with cols[4]:
        st.markdown(f"Current Week: {league.current_week}")


    with st.expander("Top Free Agents For Full Season using FantasyPros Projections"):
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

    st.subheader("Top Free Agents For Week by Projected Points using ESPN Projections")

    free_agents_week = list(league.free_agents(size=1000, week=week_number))

    player_dict = {}
    for player in free_agents_week:
        attributes = player.__dict__
        player_dict[player.name] = attributes

    free_agents_week_df = pd.DataFrame.from_dict(player_dict, orient="index")
    free_agents_week_df = free_agents_week_df[["name", "projected_points", "position", "posRank", "proTeam", "injuryStatus", "percent_owned"]]
    free_agents_week_df["Count by Position"] = free_agents_week_df["position"].map(free_agents_week_df["position"].value_counts())
    free_agents_week_df = free_agents_week_df[free_agents_week_df["Count by Position"] >= 2]

    # Drop rows where projected_points is less than 0.1
    free_agents_week_df = free_agents_week_df[free_agents_week_df["projected_points"] >= 0.1]

    free_agents_week_df.sort_values("projected_points", ascending=False, inplace=True)

    unique_positions = free_agents_week_df["position"].unique()

    box_scores = league.box_scores(week=week_number)

    selected_roster = None
    for box_score in box_scores:
        if box_score.home_team.team_id == st.session_state["selected_team"].team_id:
            selected_roster = box_score.home_lineup
            break
        elif box_score.away_team.team_id == st.session_state["selected_team"].team_id:
            selected_roster = box_score.away_lineup
            break
    with st.expander(f"Your Team's Roster for Week {week_number}:"):
        roster_dict = {}
        for player in selected_roster:
            roster_dict[player.name] = player.__dict__
        roster_df = pd.DataFrame.from_dict(roster_dict, orient="index")
        roster_df = roster_df[["name", "projected_points", "position", "posRank", "proTeam", "injuryStatus"]]
        st.dataframe(roster_df, hide_index=True)

    cols = st.columns(len(unique_positions))

    for col, pos in zip(cols, unique_positions):
        with col:
            st.subheader(pos)
            st.dataframe(free_agents_week_df[free_agents_week_df["position"] == pos], hide_index=True, height=160)
            max_proj_points = free_agents_week_df[free_agents_week_df['position'] == pos]['projected_points'].max()
            max_player_name = free_agents_week_df[free_agents_week_df['position'] == pos][free_agents_week_df['position'] == pos]['name'].values[0]
            st.write(f"Most Projected Points: {max_proj_points}\n({max_player_name})")

            roster_position_df = roster_df[roster_df["position"] == pos]
            roster_position_df["improvement"] = max_proj_points - roster_position_df["projected_points"]
            roster_position_df = roster_position_df[roster_position_df["improvement"] > 0]
            # Count the number of players in the free agent pool that are better options than this row
            roster_position_df["# Options"] = roster_position_df.apply(
                lambda row: (free_agents_week_df[
                    (free_agents_week_df["position"] == pos) &
                    (free_agents_week_df["projected_points"] > row["projected_points"])
                ].shape[0]), axis=1)

            st.markdown(f"###### Potential Improvement:")
            improvement_df = roster_position_df[["name", "improvement", "# Options"]].sort_values(by="improvement", ascending=False)
            st.dataframe(improvement_df, hide_index=True)

st.set_page_config(page_title="Free Agents in ESPN", layout="wide")
free_agents_espn_tab()
