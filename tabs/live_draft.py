import streamlit as st
import pandas as pd

HEAD_COUNT = 5

# Load data
st.session_state["dst_data"] = pd.read_csv("./data_tables/FantasyPros_Fantasy_Football_Projections_DST.csv")
st.session_state["flx_data"] = pd.read_csv("./data_tables/FantasyPros_Fantasy_Football_Projections_FLX.csv")
st.session_state["k_data"] = pd.read_csv("./data_tables/FantasyPros_Fantasy_Football_Projections_K.csv")
st.session_state["qb_data"] = pd.read_csv("./data_tables/FantasyPros_Fantasy_Football_Projections_QB.csv")
st.session_state["adp_data"] = pd.read_csv("./data_tables/FantasyPros_2025_Overall_ADP_Rankings.csv", on_bad_lines='skip')

def live_draft_tab():

    combined_data = st.session_state["combined_data"]
    
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

    adp_df = combined_data[["Player", "POS", "ADP", "Drafted"]]
    vorp_df = combined_data[["Player", "POS", "VORP", "VORP_Rank", "VORP_Value_Against_ADP", "Drafted"]]
    vobb_df = combined_data[["Player", "POS", "VOBP", "VOBP_Rank", "VOBP_Value_Against_ADP", "Drafted"]]

    # Highlight drafted players in yellow
    def highlight_drafted(row):
        color = "background-color: yellow" if row["Drafted"] else ""
        return [color] * len(row)

    cols = st.columns(3)
    with cols[0]:
        st.subheader("ADP")

        # Format the ADP column
        adp_df["ADP"] = adp_df["ADP"].map("{:,.2f}".format)

        st.dataframe(
            adp_df.sort_values(by="ADP", ascending=True).style.apply(highlight_drafted, axis=1),
            hide_index=True,
            height=200
        )

    with cols[1]:
        st.subheader("VORP")
        st.dataframe(
            vorp_df.sort_values(by="VORP", ascending=False).style.apply(highlight_drafted, axis=1),
            hide_index=True,
            height=200
        )

    with cols[2]:
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

