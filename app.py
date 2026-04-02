import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="LoL Player Analyzer", layout="wide")
st.title("LoL Player Analyzer")

api_key = st.secrets["RIOT_API_KEY"]
headers = {"X-Riot-Token": api_key}

# ----------------------------
# Helper functions
# ----------------------------

def classify_match_type(queue_id, game_mode):
    # Common queue IDs
    # 420 = Ranked Solo/Duo
    # 440 = Ranked Flex
    # 450 = ARAM
    # 400 = Normal Draft
    # 430 = Normal Blind
    if queue_id in [420, 440]:
        return "Ranked"
    elif queue_id == 450 or game_mode == "ARAM":
        return "ARAM"
    elif queue_id in [400, 430]:
        return "Normals"
    else:
        return "Other"

def normalize_role(role_value):
    if not role_value:
        return "UNKNOWN"
    role_value = role_value.upper()
    if role_value in ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]:
        return role_value
    return "UNKNOWN"

def display_role_name(role_value):
    role_map = {
        "TOP": "Top",
        "JUNGLE": "Jungle",
        "MIDDLE": "Mid",
        "BOTTOM": "ADC",
        "UTILITY": "Support",
        "UNKNOWN": "Unknown"
    }
    return role_map.get(role_value, role_value)

# ----------------------------
# UI inputs
# ----------------------------

game_name = st.text_input("Riot ID name", "HE TAKE ME")
tag_line = st.text_input("Riot ID tag", "OHNO")
match_count = st.slider("How many recent matches to analyze?", 5, 30, 15)

match_type_filter = st.selectbox(
    "Match type filter",
    ["All", "Ranked", "Normals", "ARAM"]
)

role_filter = st.selectbox(
    "Role filter",
    ["All", "Top", "Jungle", "Mid", "ADC", "Support"]
)

# ----------------------------
# Main button
# ----------------------------

if st.button("Analyze Player"):
    account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    account_response = requests.get(account_url, headers=headers)

    st.write("Account status code:", account_response.status_code)

    if account_response.status_code != 200:
        try:
            st.json(account_response.json())
        except Exception:
            st.write(account_response.text)
        st.stop()

    account_data = account_response.json()
    puuid = account_data["puuid"]

    matches_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={match_count}"
    matches_response = requests.get(matches_url, headers=headers)

    st.write("Match list status code:", matches_response.status_code)

    if matches_response.status_code != 200:
        try:
            st.json(matches_response.json())
        except Exception:
            st.write(matches_response.text)
        st.stop()

    match_ids = matches_response.json()

    rows = []

    for match_id in match_ids:
        match_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"
        match_response = requests.get(match_url, headers=headers)

        if match_response.status_code != 200:
            continue

        match_data = match_response.json()
        info = match_data.get("info", {})
        participants = info.get("participants", [])

        player_data = None
        for participant in participants:
            if participant.get("puuid") == puuid:
                player_data = participant
                break

        if player_data is None:
            continue

        kills = player_data.get("kills", 0)
        deaths = player_data.get("deaths", 0)
        assists = player_data.get("assists", 0)
        role_raw = normalize_role(player_data.get("teamPosition", "UNKNOWN"))
        role_display = display_role_name(role_raw)

        queue_id = info.get("queueId", -1)
        game_mode = info.get("gameMode", "Unknown")
        match_type = classify_match_type(queue_id, game_mode)

        rows.append({
            "match_id": match_id,
            "champion": player_data.get("championName", "Unknown"),
            "role_raw": role_raw,
            "role": role_display,
            "win": player_data.get("win", False),
            "kills": kills,
            "deaths": deaths,
            "assists": assists,
            "kda": round((kills + assists) / max(1, deaths), 2),
            "cs": player_data.get("totalMinionsKilled", 0) + player_data.get("neutralMinionsKilled", 0),
            "vision_score": player_data.get("visionScore", 0),
            "damage_to_champs": player_data.get("totalDamageDealtToChampions", 0),
            "game_mode": game_mode,
            "queue_id": queue_id,
            "match_type": match_type,
            "game_duration_min": round(info.get("gameDuration", 0) / 60, 1)
        })

    if not rows:
        st.warning("No match details could be loaded.")
        st.stop()

    df = pd.DataFrame(rows)

    # ----------------------------
    # Apply filters
    # ----------------------------

    filtered_df = df.copy()

    if match_type_filter != "All":
        filtered_df = filtered_df[filtered_df["match_type"] == match_type_filter]

    role_map_filter = {
        "Top": "Top",
        "Jungle": "Jungle",
        "Mid": "Mid",
        "ADC": "ADC",
        "Support": "Support"
    }

    if role_filter != "All":
        filtered_df = filtered_df[filtered_df["role"] == role_map_filter[role_filter]]

    if filtered_df.empty:
        st.warning("No matches found for that filter combination.")
        st.stop()

    # ----------------------------
    # Main table
    # ----------------------------

    st.subheader("Filtered Match Details")
    st.dataframe(filtered_df, use_container_width=True)

    # ----------------------------
    # Quick summary
    # ----------------------------

    total_games = len(filtered_df)
    total_wins = int(filtered_df["win"].sum())
    total_losses = total_games - total_wins
    overall_winrate = round((total_wins / total_games) * 100, 1)

    st.subheader("Quick Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Games", total_games)
    col2.metric("Wins", total_wins)
    col3.metric("Losses", total_losses)
    col4.metric("Win Rate", f"{overall_winrate}%")

    col5, col6, col7 = st.columns(3)
    col5.metric("Avg KDA", round(filtered_df["kda"].mean(), 2))
    col6.metric("Avg CS", round(filtered_df["cs"].mean(), 1))
    col7.metric("Avg Damage", int(filtered_df["damage_to_champs"].mean()))

    # ----------------------------
    # Champion summary
    # ----------------------------

    champion_summary = (
        filtered_df.groupby("champion")
        .agg(
            games=("champion", "count"),
            wins=("win", "sum"),
            avg_kda=("kda", "mean"),
            avg_cs=("cs", "mean"),
            avg_damage=("damage_to_champs", "mean")
        )
        .reset_index()
    )

    champion_summary["losses"] = champion_summary["games"] - champion_summary["wins"]
    champion_summary["win_rate"] = round((champion_summary["wins"] / champion_summary["games"]) * 100, 1)
    champion_summary["avg_kda"] = champion_summary["avg_kda"].round(2)
    champion_summary["avg_cs"] = champion_summary["avg_cs"].round(1)
    champion_summary["avg_damage"] = champion_summary["avg_damage"].round(0)

    st.subheader("Champion Summary")
    st.dataframe(
        champion_summary.sort_values(by=["games", "win_rate"], ascending=[False, False]),
        use_container_width=True
    )

    # ----------------------------
    # Role summary
    # ----------------------------

    role_summary = (
        df.groupby("role")
        .agg(
            games=("role", "count"),
            wins=("win", "sum"),
            avg_kda=("kda", "mean")
        )
        .reset_index()
    )

    role_summary["win_rate"] = round((role_summary["wins"] / role_summary["games"]) * 100, 1)
    role_summary["avg_kda"] = role_summary["avg_kda"].round(2)

    st.subheader("Role Summary (all loaded matches)")
    st.dataframe(
        role_summary.sort_values(by="games", ascending=False),
        use_container_width=True
    )

    # ----------------------------
    # Charts
    # ----------------------------

    st.subheader("Charts")

    top_champs = champion_summary.sort_values(by="games", ascending=False).head(8)
    top_wr = champion_summary[champion_summary["games"] >= 1].sort_values(by="win_rate", ascending=False).head(8)

    if not top_champs.empty:
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        ax1.bar(top_champs["champion"], top_champs["games"])
        ax1.set_title("Top Champions by Games Played")
        ax1.set_xlabel("Champion")
        ax1.set_ylabel("Games")
        plt.xticks(rotation=45)
        st.pyplot(fig1)

    if not top_wr.empty:
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.bar(top_wr["champion"], top_wr["win_rate"])
        ax2.set_title("Top Champion Win Rates")
        ax2.set_xlabel("Champion")
        ax2.set_ylabel("Win Rate %")
        plt.xticks(rotation=45)
        st.pyplot(fig2)
