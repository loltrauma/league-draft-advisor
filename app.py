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
        max-width: 1250px;
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

    .champ-card {
        padding: 0.75rem;
        border-radius: 18px;
        background: rgba(17, 24, 39, 0.90);
        border: 1px solid rgba(212, 175, 55, 0.16);
        box-shadow: 0 8px 22px rgba(0,0,0,0.22);
        margin-bottom: 1rem;
    }

    .champ-name {
        font-size: 1rem;
        font-weight: 700;
        color: #f8e7b0;
        margin-top: 0.45rem;
        margin-bottom: 0.25rem;
    }

    .champ-stat {
        font-size: 0.92rem;
        color: #d1d5db;
        line-height: 1.5;
    }

    .match-card-win {
        padding: 0.65rem 0.8rem;
        border-radius: 14px;
        background: rgba(220, 252, 231, 0.18);
        border: 1px solid rgba(134, 239, 172, 0.35);
        box-shadow: 0 6px 14px rgba(0,0,0,0.14);
        color: #dcfce7;
        margin-bottom: 0.65rem;
    }

    .match-card-loss {
        padding: 0.65rem 0.8rem;
        border-radius: 14px;
        background: rgba(254, 226, 226, 0.16);
        border: 1px solid rgba(252, 165, 165, 0.35);
        box-shadow: 0 6px 14px rgba(0,0,0,0.14);
        color: #fee2e2;
        margin-bottom: 0.65rem;
    }

    .match-title {
        font-size: 0.98rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .match-line {
        font-size: 0.84rem;
        line-height: 1.35;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-card">
    <div class="hero-title">LoL Draft & Player Analyzer</div>
    <div class="hero-subtitle">
        Arcane-inspired mood, cleaner visuals, compact champion art, and real Riot API match analysis.
        Filter by match type and role, review champion trends, and build toward a smarter draft recommendation tool.
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
@st.cache_data(show_spinner=False)
def get_latest_ddragon_version():
    url = "https://ddragon.leagueoflegends.com/api/versions.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    versions = response.json()
    return versions[0]


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


def champion_to_ddragon_name(champion_name):
    special_map = {
        "FiddleSticks": "Fiddlesticks",
        "MonkeyKing": "MonkeyKing",
        "KogMaw": "KogMaw",
        "KhaZix": "Khazix",
        "RekSai": "RekSai",
        "Belveth": "Belveth",
        "Velkoz": "Velkoz",
        "TahmKench": "TahmKench",
        "AurelionSol": "AurelionSol",
        "LeeSin": "LeeSin",
        "JarvanIV": "JarvanIV",
        "MissFortune": "MissFortune",
        "XinZhao": "XinZhao",
        "TwistedFate": "TwistedFate",
        "MasterYi": "MasterYi",
        "DrMundo": "DrMundo",
        "Nunu": "Nunu",
        "Renata": "Renata",
        "Tahm Kench": "TahmKench",
        "LeBlanc": "Leblanc",
        "Cho'Gath": "Chogath",
        "Kai'Sa": "Kaisa",
        "K'Sante": "KSante",
        "Vel'Koz": "Velkoz",
        "Bel'Veth": "Belveth",
        "Rek'Sai": "RekSai",
        "Kha'Zix": "Khazix",
    }
    return special_map.get(champion_name, champion_name)


def get_champion_splash_url(champion_name):
    champ = champion_to_ddragon_name(champion_name)
    return f"https://ddragon.leagueoflegends.com/cdn/img/champion/loading/{champ}_0.jpg"


def get_champion_square_url(champion_name):
    version = get_latest_ddragon_version()
    champ = champion_to_ddragon_name(champion_name)
    return f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champ}.png"


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
            f"{height:.1f}",
            ha="center",
            va="bottom",
            color="#f8e7b0",
            fontsize=9,
            fontweight="bold"
        )

    plt.tight_layout()
    return fig


def render_champion_cards(champion_summary_df):
    cards = champion_summary_df.sort_values(
        by=["games", "win_rate"], ascending=[False, False]
    ).head(8).to_dict("records")

    for i in range(0, len(cards), 4):
        row_cards = cards[i:i + 4]
        cols = st.columns(4)
        for col, card in zip(cols, row_cards):
            with col:
                splash_url = get_champion_splash_url(card["champion"])
                st.markdown('<div class="champ-card">', unsafe_allow_html=True)
                st.image(splash_url, use_container_width=True)
                st.markdown(f'<div class="champ-name">{card["champion"]}</div>', unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div class="champ-stat">
                        Games: {int(card["games"])}<br>
                        Win Rate: {card["win_rate"]}%<br>
                        Avg KDA: {card["avg_kda"]}<br>
                        Avg CS: {card["avg_cs"]}<br>
                        Avg Damage: {int(card["avg_damage"])}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown('</div>', unsafe_allow_html=True)


def render_recent_match_rows(filtered_df):
    records = filtered_df.sort_values(by="match_id", ascending=False).to_dict("records")

    for match in records:
        icon_url = get_champion_square_url(match["champion"])
        card_class = "match-card-win" if match["win"] else "match-card-loss"
        result_text = "WIN" if match["win"] else "LOSS"

        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns([0.8, 2.2, 1.2, 1.4, 1.8])

        with col1:
            st.image(icon_url, width=52)

        with col2:
            st.markdown(
                f"""
                <div class="match-title" style="margin-bottom: 0.1rem;">{match["champion"]}</div>
                <div class="match-line">{match["role"]} • {match["match_type"]}</div>
                """,
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                f"""
                <div class="match-title" style="font-size: 0.95rem;">{result_text}</div>
                <div class="match-line">{match["game_duration_min"]} min</div>
                """,
                unsafe_allow_html=True
            )

        with col4:
            st.markdown(
                f"""
                <div class="match-line">K / D / A</div>
                <div class="match-title" style="font-size: 0.95rem;">{match["kills"]} / {match["deaths"]} / {match["assists"]}</div>
                """,
                unsafe_allow_html=True
            )

        with col5:
            st.markdown(
                f"""
                <div class="match-line">KDA: {match["kda"]}</div>
                <div class="match-line">CS: {match["cs"]} • Vision: {match["vision_score"]}</div>
                <div class="match-line">Dmg: {int(match["damage_to_champs"])}</div>
                """,
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)


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

        filtered_df = df.copy()

        if match_type_filter != "All":
            filtered_df = filtered_df[filtered_df["match_type"] == match_type_filter]

        if role_filter != "All":
            filtered_df = filtered_df[filtered_df["role"] == role_filter]

        if filtered_df.empty:
            st.warning("No matches found for that filter combination.")
            st.stop()

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

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Top Champions")
        render_champion_cards(champion_summary)
        st.markdown('</div>', unsafe_allow_html=True)

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

        tab1, tab2, tab3 = st.tabs(["Recent Matches", "Champion Summary", "Role Summary"])

        with tab1:
            render_recent_match_rows(filtered_df)

        with tab2:
            champion_display = champion_summary.copy()
            champion_display["champion_art"] = champion_display["champion"].apply(get_champion_square_url)
            champion_display = champion_display[
                ["champion_art", "champion", "games", "wins", "losses", "win_rate", "avg_kda", "avg_cs", "avg_damage"]
            ]
            st.dataframe(
                champion_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "champion_art": st.column_config.ImageColumn("Champion", width="small"),
                    "champion": "Name",
                    "games": "Games",
                    "wins": "Wins",
                    "losses": "Losses",
                    "win_rate": "Win Rate %",
                    "avg_kda": "Avg KDA",
                    "avg_cs": "Avg CS",
                    "avg_damage": "Avg Damage"
                }
            )

        with tab3:
            st.dataframe(
                role_summary.sort_values(by="games", ascending=False),
                use_container_width=True,
                hide_index=True
            )

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Toward the Draft Recommender Vision")
        st.write(
            "This is now strong enough to build the next layer: recommend the best champion from a player’s pool "
            "based on selected role, match type, recent form, and champion performance. "
            "After that, add matchup-aware scoring and S / A / B tier recommendations."
        )
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Use the left sidebar to enter a Riot ID, choose filters, and click Analyze Player.")
