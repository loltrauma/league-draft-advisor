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
# Styling
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
        padding-top: 1.3rem;
        padding-bottom: 2rem;
        max-width: 1320px;
    }

    h1, h2, h3 {
        color: #f8e7b0;
        letter-spacing: 0.3px;
    }

    .hero-card {
        padding: 1.15rem 1.4rem;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(20,29,48,0.95), rgba(15,23,42,0.88));
        border: 1px solid rgba(212, 175, 55, 0.25);
        box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        margin-bottom: 1rem;
    }

    .hero-title {
        font-size: 1.95rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
        color: #f8e7b0;
    }

    .hero-subtitle {
        font-size: 0.96rem;
        color: #d1d5db;
        line-height: 1.55;
    }

    .section-card {
        padding: 0.95rem 1rem;
        border-radius: 18px;
        background: rgba(17, 24, 39, 0.82);
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 8px 24px rgba(0,0,0,0.20);
        margin-bottom: 0.95rem;
    }

    .small-note {
        color: #cbd5e1;
        font-size: 0.9rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.90);
        border: 1px solid rgba(212, 175, 55, 0.18);
        padding: 0.85rem;
        border-radius: 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.18);
    }

    div[data-testid="stMetricLabel"] {
        color: #d1d5db;
    }

    div[data-testid="stMetricValue"] {
        color: #f8e7b0;
    }

    .match-card-win {
        padding: 0.72rem 0.82rem;
        border-radius: 14px;
        background: rgba(34, 197, 94, 0.26);
        border: 1px solid rgba(134, 239, 172, 0.60);
        box-shadow: 0 6px 14px rgba(0,0,0,0.16);
        color: #ecfdf5;
        margin-bottom: 0.65rem;
    }

    .match-card-loss {
        padding: 0.72rem 0.82rem;
        border-radius: 14px;
        background: rgba(239, 68, 68, 0.24);
        border: 1px solid rgba(252, 165, 165, 0.62);
        box-shadow: 0 6px 14px rgba(0,0,0,0.16);
        color: #fef2f2;
        margin-bottom: 0.65rem;
    }

    .match-title {
        font-size: 0.98rem;
        font-weight: 800;
        margin-bottom: 0.15rem;
    }

    .match-line {
        font-size: 0.84rem;
        line-height: 1.35;
        font-weight: 600;
    }

    .tier-card {
        padding: 0.85rem;
        border-radius: 16px;
        background: rgba(17, 24, 39, 0.88);
        border: 1px solid rgba(212, 175, 55, 0.15);
        box-shadow: 0 6px 18px rgba(0,0,0,0.18);
        min-height: 240px;
    }

    .tier-header {
        font-size: 1.1rem;
        font-weight: 800;
        margin-bottom: 0.65rem;
    }

    .tier-chip {
        display: inline-block;
        padding: 0.25rem 0.55rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
        margin-bottom: 0.55rem;
        color: #0f172a;
        background: #f8e7b0;
    }

    .tier-line {
        font-size: 0.9rem;
        line-height: 1.55;
        color: #e5e7eb;
        margin-bottom: 0.5rem;
    }

    .mastery-card {
        text-align: center;
        padding: 0.55rem;
        border-radius: 14px;
        background: rgba(17, 24, 39, 0.88);
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 6px 14px rgba(0,0,0,0.14);
    }

    .mastery-name {
        font-size: 0.82rem;
        font-weight: 700;
        color: #f8e7b0;
        margin-top: 0.3rem;
        margin-bottom: 0.15rem;
    }

    .mastery-stat {
        font-size: 0.72rem;
        color: #cbd5e1;
        line-height: 1.35;
    }

    .context-note {
        font-size: 0.82rem;
        color: #cbd5e1;
        margin-top: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-card">
    <div class="hero-title">LoL Draft & Player Analyzer</div>
    <div class="hero-subtitle">
        Queue-aware player analysis with compact match history, player-specific champion tiers,
        ranked context, and a mastery strip built to evolve into a draft recommender.
    </div>
</div>
""", unsafe_allow_html=True)

api_key = st.secrets["RIOT_API_KEY"]
headers = {"X-Riot-Token": api_key}

# ----------------------------
# Helpers
# ----------------------------
@st.cache_data(show_spinner=False)
def get_latest_ddragon_version():
    response = requests.get("https://ddragon.leagueoflegends.com/api/versions.json", timeout=10)
    response.raise_for_status()
    return response.json()[0]

def classify_match_type(queue_id, game_mode):
    if queue_id == 420:
        return "Ranked Solo"
    elif queue_id == 440:
        return "Ranked Flex"
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

def get_champion_square_url(champion_name):
    version = get_latest_ddragon_version()
    champ = champion_to_ddragon_name(champion_name)
    return f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champ}.png"

def make_bar_chart(labels, values, title, ylabel, color="#c8a75d"):
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    fig.patch.set_facecolor("#111827")
    ax.set_facecolor("#111827")

    bars = ax.bar(labels, values, color=color, edgecolor="#f8e7b0", linewidth=1.0)

    ax.set_title(title, color="#f8e7b0", fontsize=14, pad=12, fontweight="bold")
    ax.set_ylabel(ylabel, color="#d1d5db")
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
            fontsize=8.5,
            fontweight="bold"
        )

    plt.tight_layout()
    return fig

def format_rank(entry):
    if not entry:
        return "Unavailable"
    return f'{entry.get("tier", "")} {entry.get("rank", "")} • {entry.get("leaguePoints", 0)} LP'

def compute_recent_form(filtered_df, champion_name):
    champ_games = filtered_df[filtered_df["champion"] == champion_name].copy()
    if champ_games.empty:
        return 0.0
    champ_games = champ_games.head(min(5, len(champ_games)))
    recent_wr = champ_games["win"].mean() * 100
    recent_kda = champ_games["kda"].mean()
    return (recent_wr * 0.7) + (min(recent_kda, 8) / 8 * 30)

def build_tiers(champion_summary, filtered_df):
    if champion_summary.empty:
        return champion_summary

    working = champion_summary.copy()
    max_games = working["games"].max() if working["games"].max() > 0 else 1
    max_kda = working["avg_kda"].max() if working["avg_kda"].max() > 0 else 1

    scores = []
    for _, row in working.iterrows():
        recent_form = compute_recent_form(filtered_df, row["champion"])
        normalized_games = (row["games"] / max_games) * 100
        normalized_kda = (row["avg_kda"] / max_kda) * 100 if max_kda > 0 else 0

        score = (
            row["win_rate"] * 0.45 +
            normalized_games * 0.25 +
            normalized_kda * 0.20 +
            recent_form * 0.10
        )
        scores.append(round(score, 1))

    working["tier_score"] = scores

    def score_to_tier(score):
        if score >= 78:
            return "S"
        elif score >= 68:
            return "A"
        elif score >= 58:
            return "B"
        else:
            return "C"

    working["tier"] = working["tier_score"].apply(score_to_tier)
    return working.sort_values(by=["tier_score", "games"], ascending=[False, False])

def render_recent_match_rows(filtered_df):
    records = filtered_df.sort_values(by="match_id", ascending=False).to_dict("records")

    for match in records:
        icon_url = get_champion_square_url(match["champion"])
        card_class = "match-card-win" if match["win"] else "match-card-loss"
        result_text = "WIN" if match["win"] else "LOSS"

        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns([0.8, 2.2, 1.2, 1.4, 1.9])

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

def render_mastery_strip(champion_summary_df):
    top7 = champion_summary_df.sort_values(by=["games", "win_rate"], ascending=[False, False]).head(7).to_dict("records")
    cols = st.columns(7)

    for col, card in zip(cols, top7):
        with col:
            st.markdown('<div class="mastery-card">', unsafe_allow_html=True)
            st.image(get_champion_square_url(card["champion"]), width=58)
            st.markdown(f'<div class="mastery-name">{card["champion"]}</div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="mastery-stat">
                    {int(card["games"])} games<br>
                    {card["win_rate"]}% WR
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

def render_tier_column(df_tiers, tier_label, chip_text):
    st.markdown('<div class="tier-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="tier-header">{tier_label} Tier</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="tier-chip">{chip_text}</div>', unsafe_allow_html=True)

    subset = df_tiers[df_tiers["tier"] == tier_label].head(5)
    if subset.empty:
        st.markdown('<div class="tier-line">No champions in this tier yet.</div>', unsafe_allow_html=True)
    else:
        for _, row in subset.iterrows():
            st.markdown(
                f"""
                <div class="tier-line">
                    <strong>{row["champion"]}</strong><br>
                    Score: {row["tier_score"]} • WR: {row["win_rate"]}% • Games: {int(row["games"])} • KDA: {row["avg_kda"]}
                </div>
                """,
                unsafe_allow_html=True
            )
    st.markdown('</div>', unsafe_allow_html=True)

def fetch_filtered_matches(puuid, selected_match_type, selected_role, desired_count):
    """
    Pull recent match IDs in chunks, then keep only matches matching the selected type/role
    until we have the desired number.
    """
    collected_rows = []
    start = 0
    chunk_size = 100
    max_scan = 400

    while len(collected_rows) < desired_count and start < max_scan:
        ids_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={chunk_size}"
        ids_response = requests.get(ids_url, headers=headers, timeout=20)

        if ids_response.status_code != 200:
            break

        match_ids = ids_response.json()
        if not match_ids:
            break

        for match_id in match_ids:
            if len(collected_rows) >= desired_count:
                break

            match_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"
            match_response = requests.get(match_url, headers=headers, timeout=20)

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

            queue_id = info.get("queueId", -1)
            game_mode = info.get("gameMode", "Unknown")
            match_type = classify_match_type(queue_id, game_mode)

            role_raw = normalize_role(player_data.get("teamPosition", "UNKNOWN"))
            role_display = display_role_name(role_raw)

            if selected_match_type != "All" and match_type != selected_match_type:
                continue

            if selected_role != "All" and role_display != selected_role:
                continue

            kills = player_data.get("kills", 0)
            deaths = player_data.get("deaths", 0)
            assists = player_data.get("assists", 0)

            collected_rows.append({
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
                "queue_id": queue_id,
                "game_duration_min": round(info.get("gameDuration", 0) / 60, 1)
            })

        start += chunk_size

    return pd.DataFrame(collected_rows)

# ----------------------------
# Sidebar
# ----------------------------
st.sidebar.header("Player & Filter Controls")

game_name = st.sidebar.text_input("Riot ID name", "HE TAKE ME")
tag_line = st.sidebar.text_input("Riot ID tag", "OHNO")

match_type_filter = st.sidebar.selectbox(
    "Queue / Match type",
    ["All", "Ranked Solo", "Ranked Flex", "Normals", "ARAM"]
)

role_filter = st.sidebar.selectbox(
    "Role",
    ["All", "Top", "Jungle", "Mid", "ADC", "Support"]
)

analyze_clicked = st.sidebar.button("Analyze Player", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<div class="small-note">Tip: Ranked Solo + one role gives the cleanest signal for champion recommendations.</div>',
    unsafe_allow_html=True
)

# ----------------------------
# Session state for pagination
# ----------------------------
filter_key = f"{game_name}|{tag_line}|{match_type_filter}|{role_filter}"

if "current_filter_key" not in st.session_state:
    st.session_state.current_filter_key = filter_key

if "games_to_show" not in st.session_state:
    st.session_state.games_to_show = 20

if filter_key != st.session_state.current_filter_key:
    st.session_state.current_filter_key = filter_key
    st.session_state.games_to_show = 20

load_more_clicked = st.sidebar.button("Load More Games", use_container_width=True)
if load_more_clicked:
    st.session_state.games_to_show += 20

# ----------------------------
# Main
# ----------------------------
if analyze_clicked or "last_loaded_filter_key" in st.session_state:
    st.session_state.last_loaded_filter_key = filter_key

    with st.spinner("Pulling Riot data and building your profile..."):
        account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        account_response = requests.get(account_url, headers=headers, timeout=20)

        if account_response.status_code != 200:
            st.error(f"Account lookup failed. Status code: {account_response.status_code}")
            try:
                st.json(account_response.json())
            except Exception:
                st.write(account_response.text)
            st.stop()

        puuid = account_response.json()["puuid"]

        # rank context
        solo_entry = None
        flex_entry = None
        rank_context_available = False

        summoner_url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        summoner_response = requests.get(summoner_url, headers=headers, timeout=20)

        if summoner_response.status_code == 200:
            summoner_data = summoner_response.json()
            summoner_id = summoner_data.get("id")

            if summoner_id:
                league_url = f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
                league_response = requests.get(league_url, headers=headers, timeout=20)

                if league_response.status_code == 200:
                    league_entries = league_response.json()
                    if isinstance(league_entries, list):
                        solo_entry = next((e for e in league_entries if e.get("queueType") == "RANKED_SOLO_5x5"), None)
                        flex_entry = next((e for e in league_entries if e.get("queueType") == "RANKED_FLEX_SR"), None)
                        rank_context_available = True

        # Automatically fetch enough filtered games based on selected type/role
        filtered_df = fetch_filtered_matches(
            puuid=puuid,
            selected_match_type=match_type_filter,
            selected_role=role_filter,
            desired_count=st.session_state.games_to_show
        )

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

        tier_df = build_tiers(champion_summary, filtered_df)

        role_summary = (
            filtered_df.groupby("role")
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

        # Layout: left snapshot column, right main content
        left_col, right_col = st.columns([1, 2.4], gap="large")

        with left_col:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Performance Snapshot")
            st.metric("Games", total_games)
            st.metric("Wins", total_wins)
            st.metric("Losses", total_losses)
            st.metric("Win Rate", f"{overall_winrate}%")
            st.metric("Avg KDA", round(filtered_df["kda"].mean(), 2))
            st.metric("Avg CS", round(filtered_df["cs"].mean(), 1))
            st.metric("Avg Damage", int(filtered_df["damage_to_champs"].mean()))
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Matchmaking Context")
            st.metric("Current Solo Queue Rank", format_rank(solo_entry))
            st.metric("Current Flex Queue Rank", format_rank(flex_entry))
            if rank_context_available:
                st.write("Rank context loaded successfully.")
            else:
                st.write("Rank context unavailable for this player or this request.")
            st.markdown(
                '<div class="context-note">This uses ranked queue data as context only. Duo/premade effects can influence matchmaking, so treat this as a rank-based proxy, not true hidden MMR.</div>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with right_col:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader(f"Recent Matches ({len(filtered_df)} loaded)")
            render_recent_match_rows(filtered_df)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Player-Specific Champion Tiers")
            t1, t2, t3, t4 = st.columns(4)
            with t1:
                render_tier_column(tier_df, "S", "Best current picks")
            with t2:
                render_tier_column(tier_df, "A", "Strong comfort options")
            with t3:
                render_tier_column(tier_df, "B", "Playable but lower confidence")
            with t4:
                render_tier_column(tier_df, "C", "Low confidence / tiny sample")
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
                        "Top Champion Win Rates",
                        "Win Rate %",
                        color="#6f86a6"
                    )
                    st.pyplot(fig2)
            st.markdown('</div>', unsafe_allow_html=True)

            tab1, tab2 = st.tabs(["Champion Summary", "Role Summary"])

            with tab1:
                champion_display = tier_df.copy()
                champion_display["champion_art"] = champion_display["champion"].apply(get_champion_square_url)
                champion_display = champion_display[
                    ["champion_art", "champion", "tier", "tier_score", "games", "wins", "losses", "win_rate", "avg_kda", "avg_cs", "avg_damage"]
                ]
                st.dataframe(
                    champion_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "champion_art": st.column_config.ImageColumn("Champion", width="small"),
                        "champion": "Name",
                        "tier": "Tier",
                        "tier_score": "Score",
                        "games": "Games",
                        "wins": "Wins",
                        "losses": "Losses",
                        "win_rate": "Win Rate %",
                        "avg_kda": "Avg KDA",
                        "avg_cs": "Avg CS",
                        "avg_damage": "Avg Damage"
                    }
                )

            with tab2:
                st.dataframe(
                    role_summary.sort_values(by="games", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Champion Mastery Strip")
            render_mastery_strip(champion_summary)
            st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Use the left sidebar to enter a Riot ID, choose queue and role filters, then click Analyze Player.")
