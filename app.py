import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(
    page_title="Outdraft",
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
        padding-top: 1.0rem;
        padding-bottom: 2rem;
        max-width: 1320px;
    }

    h1, h2, h3 {
        color: #f8e7b0;
        letter-spacing: 0.2px;
    }

    .hero-card {
        padding: 1rem 1.2rem 0.85rem 1.2rem;
        border-radius: 22px;
        background: linear-gradient(135deg, rgba(20,29,48,0.95), rgba(15,23,42,0.90));
        border: 1px solid rgba(212, 175, 55, 0.24);
        box-shadow: 0 12px 30px rgba(0,0,0,0.32);
        margin-bottom: 1rem;
    }

    .hero-subtitle {
        font-size: 0.95rem;
        color: #cfd6e4;
        line-height: 1.55;
        margin-top: 0.4rem;
    }

    .section-card {
        padding: 0.95rem 1rem;
        border-radius: 18px;
        background: rgba(17, 24, 39, 0.84);
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
        margin-bottom: 0.95rem;
    }

    .subtle-text {
        color: #cbd5e1;
        font-size: 0.88rem;
        line-height: 1.45;
    }

    .filter-chip {
        display: inline-block;
        padding: 0.36rem 0.62rem;
        margin: 0 0.35rem 0.35rem 0;
        border-radius: 999px;
        background: rgba(212, 175, 55, 0.12);
        border: 1px solid rgba(212, 175, 55, 0.24);
        color: #f8e7b0;
        font-size: 0.80rem;
        font-weight: 700;
    }

    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.90);
        border: 1px solid rgba(212, 175, 55, 0.18);
        padding: 0.82rem;
        border-radius: 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.16);
    }

    div[data-testid="stMetricLabel"] {
        color: #d1d5db;
    }

    div[data-testid="stMetricValue"] {
        color: #f8e7b0;
    }

    .pick-card {
        padding: 0.9rem;
        border-radius: 18px;
        background: rgba(17, 24, 39, 0.90);
        border: 1px solid rgba(212, 175, 55, 0.18);
        box-shadow: 0 8px 22px rgba(0,0,0,0.18);
        text-align: center;
        min-height: 320px;
    }

    .pick-label {
        font-size: 0.78rem;
        color: #cbd5e1;
        margin-bottom: 0.4rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .pick-name {
        font-size: 1.05rem;
        font-weight: 800;
        color: #f8e7b0;
        margin-top: 0.45rem;
        margin-bottom: 0.15rem;
    }

    .confidence-high {
        display: inline-block;
        padding: 0.20rem 0.50rem;
        border-radius: 999px;
        background: rgba(34, 197, 94, 0.18);
        border: 1px solid rgba(134, 239, 172, 0.42);
        color: #dcfce7;
        font-size: 0.75rem;
        font-weight: 800;
        margin-bottom: 0.45rem;
    }

    .confidence-medium {
        display: inline-block;
        padding: 0.20rem 0.50rem;
        border-radius: 999px;
        background: rgba(59, 130, 246, 0.16);
        border: 1px solid rgba(147, 197, 253, 0.38);
        color: #dbeafe;
        font-size: 0.75rem;
        font-weight: 800;
        margin-bottom: 0.45rem;
    }

    .confidence-low {
        display: inline-block;
        padding: 0.20rem 0.50rem;
        border-radius: 999px;
        background: rgba(245, 158, 11, 0.16);
        border: 1px solid rgba(252, 211, 77, 0.38);
        color: #fef3c7;
        font-size: 0.75rem;
        font-weight: 800;
        margin-bottom: 0.45rem;
    }

    .pick-stat {
        font-size: 0.84rem;
        color: #d1d5db;
        line-height: 1.45;
    }

    .reason-line {
        font-size: 0.84rem;
        color: #e5e7eb;
        line-height: 1.45;
        text-align: left;
        margin-top: 0.25rem;
    }

    .tier-card {
        padding: 0.82rem;
        border-radius: 16px;
        background: rgba(17, 24, 39, 0.88);
        border: 1px solid rgba(212, 175, 55, 0.15);
        box-shadow: 0 6px 18px rgba(0,0,0,0.16);
    }

    .tier-header {
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 0.45rem;
        color: #f8e7b0;
    }

    .tier-chip {
        display: inline-block;
        padding: 0.22rem 0.5rem;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        color: #0f172a;
        background: #f8e7b0;
    }

    .tier-line {
        font-size: 0.86rem;
        line-height: 1.45;
        color: #e5e7eb;
        margin-bottom: 0.45rem;
    }

    .match-card-win {
        padding: 0.74rem 0.84rem;
        border-radius: 14px;
        background: rgba(34, 197, 94, 0.28);
        border: 1px solid rgba(134, 239, 172, 0.66);
        box-shadow: 0 6px 14px rgba(0,0,0,0.15);
        color: #ecfdf5;
        margin-bottom: 0.65rem;
    }

    .match-card-loss {
        padding: 0.74rem 0.84rem;
        border-radius: 14px;
        background: rgba(239, 68, 68, 0.25);
        border: 1px solid rgba(252, 165, 165, 0.66);
        box-shadow: 0 6px 14px rgba(0,0,0,0.15);
        color: #fef2f2;
        margin-bottom: 0.65rem;
    }

    .match-title {
        font-size: 0.96rem;
        font-weight: 800;
        margin-bottom: 0.14rem;
    }

    .match-line {
        font-size: 0.83rem;
        line-height: 1.35;
        font-weight: 600;
    }

    .mastery-card {
        text-align: center;
        padding: 0.55rem;
        border-radius: 14px;
        background: rgba(17, 24, 39, 0.88);
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 6px 14px rgba(0,0,0,0.13);
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
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Header
# ----------------------------
logo_path = Path("outdraft_logo.png")

st.markdown('<div class="hero-card">', unsafe_allow_html=True)
if logo_path.exists():
    c1, c2, c3 = st.columns([1, 2.0, 1])
    with c2:
        st.image(str(logo_path), use_container_width=True)
else:
    st.title("Outdraft")

st.markdown(
    '<div class="hero-subtitle">Built to reduce draft anxiety and surface your smartest picks fast. Outdraft focuses on clarity, confidence, and your actual champion pool.</div>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

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

def format_rank(entry):
    if not entry:
        return "Unavailable"
    return f'{entry.get("tier", "")} {entry.get("rank", "")} • {entry.get("leaguePoints", 0)} LP'

def parse_csv_text(text):
    return [x.strip() for x in text.split(",") if x.strip()]

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

def build_recommendations(tier_df, ally_picks, enemy_picks, bans):
    if tier_df.empty:
        return pd.DataFrame()

    unavailable = set(ally_picks + enemy_picks + bans)
    recs = tier_df[~tier_df["champion"].isin(unavailable)].copy()

    if recs.empty:
        return recs

    max_games = recs["games"].max() if recs["games"].max() > 0 else 1

    recs["comfort_score"] = (
        recs["tier_score"] * 0.55 +
        (recs["games"] / max_games) * 100 * 0.45
    ).round(1)

    recs["blind_score"] = (
        recs["win_rate"] * 0.50 +
        recs["tier_score"] * 0.30 +
        (recs["games"] / max_games) * 100 * 0.20
    ).round(1)

    recs["overall_score"] = (
        recs["tier_score"] * 0.70 +
        recs["comfort_score"] * 0.20 +
        recs["blind_score"] * 0.10
    ).round(1)

    return recs.sort_values(by="overall_score", ascending=False)

def get_unique_pick(df, score_col, used):
    if df.empty:
        return None
    for _, row in df.sort_values(by=score_col, ascending=False).iterrows():
        if row["champion"] not in used:
            used.add(row["champion"])
            return row
    return None

def get_confidence_label(row):
    if row is None:
        return ("No Data", "confidence-low")
    games = int(row["games"])
    wr = float(row["win_rate"])
    if games >= 12 and wr >= 58:
        return ("High Confidence", "confidence-high")
    elif games >= 6 and wr >= 50:
        return ("Solid Confidence", "confidence-medium")
    else:
        return ("Low Sample", "confidence-low")

def generate_pick_reasons(row):
    if row is None:
        return []

    reasons = []

    if row["games"] >= 12:
        reasons.append(f'{int(row["games"])} games in this filter')
    elif row["games"] >= 6:
        reasons.append(f'{int(row["games"])} recent games on this champ')

    if row["win_rate"] >= 60:
        reasons.append(f'{row["win_rate"]}% win rate')
    elif row["win_rate"] >= 52:
        reasons.append(f'positive win rate at {row["win_rate"]}%')

    if row["avg_kda"] >= 4:
        reasons.append(f'{row["avg_kda"]} average KDA')
    elif row["avg_kda"] >= 3:
        reasons.append(f'stable {row["avg_kda"]} KDA')

    if row["tier"] == "S":
        reasons.append("top-tier fit for this context")
    elif row["tier"] == "A":
        reasons.append("strong comfort option")

    return reasons[:3]

def fetch_filtered_matches(puuid, selected_match_type, selected_role, desired_count):
    collected_rows = []
    start = 0
    chunk_size = 100
    max_scan = 500

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
    subset = df_tiers[df_tiers["tier"] == tier_label].head(5)
    if subset.empty:
        return

    st.markdown('<div class="tier-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="tier-header">{tier_label} Tier</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="tier-chip">{chip_text}</div>', unsafe_allow_html=True)

    for _, row in subset.iterrows():
        st.markdown(
            f"""
            <div class="tier-line">
                <strong>{row["champion"]}</strong><br>
                Score: {row["tier_score"]} • WR: {row["win_rate"]}% • Games: {int(row["games"])}
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

def render_pick_card(label, row, score_col):
    st.markdown('<div class="pick-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="pick-label">{label}</div>', unsafe_allow_html=True)

    if row is not None:
        conf_text, conf_class = get_confidence_label(row)
        st.image(get_champion_square_url(row["champion"]), width=90)
        st.markdown(f'<div class="pick-name">{row["champion"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="{conf_class}">{conf_text}</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="pick-stat">
                {score_col.replace("_", " ").title()}: {row[score_col]}<br>
                Tier: {row["tier"]}<br>
                Games: {int(row["games"])}<br>
                Win Rate: {row["win_rate"]}%<br>
                Avg KDA: {row["avg_kda"]}
            </div>
            """,
            unsafe_allow_html=True
        )

        reasons = generate_pick_reasons(row)
        for reason in reasons:
            st.markdown(f'<div class="reason-line">• {reason}</div>', unsafe_allow_html=True)
    else:
        st.write("No eligible champion")

    st.markdown('</div>', unsafe_allow_html=True)

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

st.sidebar.markdown("---")
st.sidebar.subheader("Draft Context")

ally_picks = parse_csv_text(st.sidebar.text_input("Ally picks", ""))
enemy_picks = parse_csv_text(st.sidebar.text_input("Enemy picks", ""))
bans = parse_csv_text(st.sidebar.text_input("Bans", ""))

analyze_clicked = st.sidebar.button("Analyze Player", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<div class="subtle-text">Tip: Start with Ranked Solo + one role. Keeping inputs simple makes the recommendations feel clearer and more trustworthy.</div>',
    unsafe_allow_html=True
)

# ----------------------------
# Session state
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
            st.stop()

        puuid = account_response.json()["puuid"]

        solo_entry = None
        flex_entry = None

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
        rec_df = build_recommendations(tier_df, ally_picks, enemy_picks, bans)

        total_games = len(filtered_df)
        total_wins = int(filtered_df["win"].sum())
        total_losses = total_games - total_wins
        overall_winrate = round((total_wins / total_games) * 100, 1)

        # Applied filters
        chips = [
            match_type_filter,
            role_filter,
            f"Last {len(filtered_df)} games"
        ]
        if ally_picks:
            chips.append("Ally: " + ", ".join(ally_picks[:3]))
        if enemy_picks:
            chips.append("Enemy: " + ", ".join(enemy_picks[:3]))
        if bans:
            chips.append("Bans: " + ", ".join(bans[:3]))

        chip_html = "".join([f'<span class="filter-chip">{chip}</span>' for chip in chips])
        st.markdown(chip_html, unsafe_allow_html=True)

        tabs = st.tabs(["Draft", "Match History", "Mastery", "Graphs"])

        with tabs[0]:
            st.subheader("Recommended Picks")

            used_champs = set()
            top_overall = get_unique_pick(rec_df, "overall_score", used_champs)
            top_comfort = get_unique_pick(rec_df, "comfort_score", used_champs)
            top_blind = get_unique_pick(rec_df, "blind_score", used_champs)

            p1, p2, p3 = st.columns(3)
            with p1:
                render_pick_card("Best Overall", top_overall, "overall_score")
            with p2:
                render_pick_card("Best Comfort", top_comfort, "comfort_score")
            with p3:
                render_pick_card("Best Blind", top_blind, "blind_score")

            present_tiers = [tier for tier in ["S", "A", "B", "C"] if not tier_df[tier_df["tier"] == tier].empty]
            if present_tiers:
                st.subheader("Tier Breakdown")
                tier_cols = st.columns(len(present_tiers))
                tier_labels = {
                    "S": "Best current picks",
                    "A": "Strong comfort options",
                    "B": "Playable options",
                    "C": "Low confidence"
                }
                for col, tier in zip(tier_cols, present_tiers):
                    with col:
                        render_tier_column(tier_df, tier, tier_labels[tier])

        with tabs[1]:
            left_col, right_col = st.columns([1, 2.2], gap="large")

            with left_col:
                st.subheader("Performance Snapshot")
                a, b = st.columns(2)
                a.metric("Games", total_games)
                b.metric("Win Rate", f"{overall_winrate}%")

                c, d = st.columns(2)
                c.metric("Wins", total_wins)
                d.metric("Losses", total_losses)

                e, f = st.columns(2)
                e.metric("Avg KDA", round(filtered_df["kda"].mean(), 2))
                f.metric("Avg CS", round(filtered_df["cs"].mean(), 1))

                st.metric("Avg Damage", int(filtered_df["damage_to_champs"].mean()))
                st.metric("Solo Rank", format_rank(solo_entry))
                st.metric("Flex Rank", format_rank(flex_entry))

            with right_col:
                st.subheader(f"Recent Matches ({len(filtered_df)} loaded)")
                render_recent_match_rows(filtered_df)

        with tabs[2]:
            st.subheader("Champion Mastery")
            render_mastery_strip(champion_summary)

            mastery_table = champion_summary.copy()
            mastery_table["champion_art"] = mastery_table["champion"].apply(get_champion_square_url)
            mastery_table = mastery_table[
                ["champion_art", "champion", "games", "wins", "losses", "win_rate", "avg_kda", "avg_cs", "avg_damage"]
            ]

            st.dataframe(
                mastery_table.sort_values(by=["games", "win_rate"], ascending=[False, False]),
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

        with tabs[3]:
            st.subheader("Graphs")

            graph_cols = st.columns(2)

            top_champs = champion_summary.sort_values(by="games", ascending=False).head(8)
            top_winrate = champion_summary.sort_values(by="win_rate", ascending=False).head(8)

            with graph_cols[0]:
                if not top_champs.empty:
                    fig1 = make_bar_chart(
                        top_champs["champion"],
                        top_champs["games"],
                        "Top Champions by Games Played",
                        "Games"
                    )
                    st.pyplot(fig1)

            with graph_cols[1]:
                if not top_winrate.empty:
                    fig2 = make_bar_chart(
                        top_winrate["champion"],
                        top_winrate["win_rate"],
                        "Top Champion Win Rates",
                        "Win Rate %",
                        color="#6f86a6"
                    )
                    st.pyplot(fig2)

else:
    st.info("Use the left sidebar to enter a Riot ID, choose queue and role filters, then click Analyze Player.")
