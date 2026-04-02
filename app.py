import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="LoL Draft & Player Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# Page styling
# ----------------------------
st.markdown("""
<style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(196,164,92,0.10), transparent 30%),
            radial-gradient(circle at top right, rgba(104,127,160,0.12), transparent 25%),
            linear-gradient(180deg, #0b1220 0%, #111827 45%, #0f172a 100%);
        color: #f3f4f6;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    h1, h2, h3 {
        color: #f8e7b0;
        letter-spacing: 0.3px;
    }

    .hero-card {
        padding: 1.5rem 1.75rem;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(20,29,48,0.95), rgba(15,23,42,0.88));
        border: 1px solid rgba(212, 175, 55, 0.25);
        box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        margin-bottom: 1.2rem;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.35rem;
        color: #f8e7b0;
    }

    .hero-subtitle {
        font-size: 1rem;
        color: #d1d5db;
        line-height: 1.6;
    }

    .section-card {
        padding: 1rem 1.1rem;
        border-radius: 18px;
        background: rgba(17, 24, 39, 0.82);
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 8px 24px rgba(0,0,0,0.20);
        margin-bottom: 1rem;
    }

    .small-note {
        color: #cbd5e1;
        font-size: 0.92rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.86);
        border: 1px solid rgba(212, 175, 55, 0.18);
        padding: 0.9rem;
        border-radius: 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.18);
    }

    div[data-testid="stMetricLabel"] {
        color: #d1d5db;
    }

    div[data-testid="stMetricValue"] {
        color: #f8e7b0;
    }

    .stDataFrame {
        border-radius: 14px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-card">
    <div class="hero-title">LoL Draft & Player Analyzer</div>
    <div class="hero-subtitle">
        Arcane-inspired mood, cleaner visuals, and real Riot API match analysis.
        Filter by match type and role, review champion trends, and build toward a smart draft recommendation tool.
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------
# Riot setup
# ----------------------------
api_key = st.secrets["RIOT_API_KEY"]
headers = {"X-Riot-Token": api_key}

# ----------------------------
# Helper functions
# ----------------------------
def classify_match_type(queue_id, game_mode):
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

def make_bar_chart(labels, values, title, ylabel, color="#c8a75d"):
    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.patch.set_facecolor("#111827")
    ax.set_facecolor("#111827")

    bars = ax.bar(labels, values, color=color, edgecolor="#f8e7b0", linewidth=1.0)

    ax.set_title(title, color="#f8e7b0", fontsize=14, pad=12, fontweight="bold")
    ax.set_ylabel(ylabel, color="#d1d5db")
    ax.set_xlabel("")
    ax.tick_params(axis="x", colors="#e5e7eb", rotation=35)
    ax.tick_params(axis="y", colors="#d1d5db")

    for spine in ax.spines.values():
        spine.set_color("#374151")

    ax.grid(axis="y", linestyle="--", alpha=0.25, color="#9ca3af")
    ax.set_axisbelow(True)

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.1f}" if isinstance(height, float) else f"{height}",
            ha="center",
            va="bottom",
            color="#f8e7b0",
            fontsize=9,
            fontweight="bold"
        )

    plt.tight_layout()
    return fig

# ----------------------------
# Sidebar controls
# ----------------------------
st.sidebar.header("Player & Filter Controls")

game_name = st.sidebar.text_input("Riot ID name", "HE TAKE ME")
tag_line = st.sidebar.text_input("Riot ID tag", "OHNO")
match_count = st.sidebar.slider("Recent matches to analyze", 5, 30, 15)

match_type_filter = st.sidebar.selectbox(
    "Match type",
    ["All", "Ranked", "Normals", "ARAM"]
)

role_filter = st.sidebar.selectbox(
    "Role",
    ["All", "Top", "Jungle", "Mid", "ADC", "Support"]
)

analyze_clicked = st.sidebar.button("Analyze Player", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<div class="small-note">Tip: start with Ranked + your main role to get the most useful champion insights.</div>',
    unsafe_allow_html=True
)

# ----------------------------
# Main logic
# ----------------------------
if analyze_clicked:
    with st.spinner("Pulling Riot match history and building your profile..."):
        account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        account_response = requests.get(account_url, headers=headers)

        if account_response.status_code != 200:
            st.error(f"Account lookup failed. Status code: {account_response.status_code}")
            try:
                st.json(account_response.json())
            except Exception:
                st.write(account_response.text)
            st.stop()

        account_data = account_response.json()
        puuid = account_data["puuid"]

        matches_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={match_count}"
        matches_response = requests.get(matches_url, headers=headers)

        if matches_response.status_code != 200:
            st.error(f"Match list lookup failed. Status code: {matches_response.status_code}")
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
                "role": role_display,
                "match_type": match_type,
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
                "game_duration_min": round(info.get("gameDuration", 0) / 60, 1)
            })

        if not rows:
            st.warning("No match details could be loaded.")
            st.stop()

        df = pd.DataFrame(rows)

        # Apply filters
        filtered_df = df.copy()

        if match_type_filter != "All":
            filtered_df = filtered_df[filtered_df["match_type"] == match_type_filter]

        if role_filter != "All":
            filtered_df = filtered_df[filtered_df["role"] == role_filter]

        if filtered_df.empty:
            st.warning("No matches found for that filter combination.")
            st.stop()

        # Champion summary
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
        champion_summary["win_rate"] = ((champion_summary["wins"] / champion_summary["games"]) * 100).round(1)
        champion_summary["avg_kda"] = champion_summary["avg_kda"].round(2)
        champion_summary["avg_cs"] = champion_summary["avg_cs"].round(1)
        champion_summary["avg_damage"] = champion_summary["avg_damage"].round(0)

        role_summary = (
            df.groupby("role")
            .agg(
                games=("role", "count"),
                wins=("win", "sum"),
                avg_kda=("kda", "mean")
            )
            .reset_index()
        )
        role_summary["win_rate"] = ((role_summary["wins"] / role_summary["games"]) * 100).round(1)
        role_summary["avg_kda"] = role_summary["avg_kda"].round(2)

        # Metrics
        total_games = len(filtered_df)
        total_wins = int(filtered_df["win"].sum())
        total_losses = total_games - total_wins
        overall_winrate = round((total_wins / total_games) * 100, 1)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Performance Snapshot")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Games", total_games)
        c2.metric("Wins", total_wins)
        c3.metric("Losses", total_losses)
        c4.metric("Win Rate", f"{overall_winrate}%")

        c5, c6, c7 = st.columns(3)
        c5.metric("Avg KDA", round(filtered_df["kda"].mean(), 2))
        c6.metric("Avg CS", round(filtered_df["cs"].mean(), 1))
        c7.metric("Avg Damage", int(filtered_df["damage_to_champs"].mean()))
        st.markdown('</div>', unsafe_allow_html=True)

        # Charts
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Champion Trends")

        chart_col1, chart_col2 = st.columns(2)

        top_champs = champion_summary.sort_values(by="games", ascending=False).head(8)
        top_winrate = champion_summary.sort_values(by="win_rate", ascending=False).head(8)

        with chart_col1:
            if not top_champs.empty:
                fig1 = make_bar_chart(
                    top_champs["champion"],
                    top_champs["games"],
                    "Top Champions by Games Played",
                    "Games"
                )
                st.pyplot(fig1)

        with chart_col2:
            if not top_winrate.empty:
                fig2 = make_bar_chart(
                    top_winrate["champion"],
                    top_winrate["win_rate"],
                    f"Top Champion Win Rates ({role_filter if role_filter != 'All' else 'Filtered'})",
                    "Win Rate %",
                    color="#6f86a6"
                )
                st.pyplot(fig2)

        st.markdown('</div>', unsafe_allow_html=True)

        # Tables
        tab1, tab2, tab3 = st.tabs(["Champion Summary", "Match Details", "Role Summary"])

        with tab1:
            st.dataframe(
                champion_summary.sort_values(by=["games", "win_rate"], ascending=[False, False]),
                use_container_width=True,
                hide_index=True
            )

        with tab2:
            st.dataframe(
                filtered_df.sort_values(by="match_id", ascending=False),
                use_container_width=True,
                hide_index=True
            )

        with tab3:
            st.dataframe(
                role_summary.sort_values(by="games", ascending=False),
                use_container_width=True,
                hide_index=True
            )

        # Draft vision note
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Toward the Draft Recommender Vision")
        st.write(
            "This foundation is now strong enough to build the next layer: recommend the best champion from a player’s pool "
            "based on selected role, match type, recent form, and champion performance. "
            "After that, you can add matchup-aware scoring and draft tiers."
        )
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Use the left sidebar to enter a Riot ID, choose filters, and click Analyze Player.")
