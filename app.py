import streamlit as st
import requests
import pandas as pd
from pathlib import Path
import time
from typing import Optional, Dict, Any

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
        background: linear-gradient(180deg, #0b1220 0%, #111827 45%, #0f172a 100%);
        color: #f3f4f6;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1320px;
    }
    .hero-card {
        background: rgba(17, 24, 39, 0.72);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 1.25rem 1.25rem 1rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    }
    .hero-subtitle {
        text-align: center;
        color: #cbd5e1;
        font-size: 1rem;
        margin-top: 0.35rem;
        margin-bottom: 1rem;
    }
    .logo-backdrop {
        background: radial-gradient(circle at center, rgba(59,130,246,0.18), rgba(255,255,255,0.02) 60%, transparent 72%);
        border-radius: 22px;
        padding: 0.8rem;
    }
    .metric-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Core config
# ----------------------------
@st.cache_data(ttl=3600)
def get_headers():
    return {"X-Riot-Token": st.secrets["RIOT_API_KEY"]}

headers = get_headers()

PLATFORM_OPTIONS = {
    "NA": "na1",
    "EUW": "euw1",
    "EUNE": "eun1",
    "KR": "kr",
    "BR": "br1",
    "LAN": "la1",
    "LAS": "la2",
    "OCE": "oc1",
    "JP": "jp1",
    "TR": "tr1",
    "RU": "ru"
}

PLATFORM_TO_REGIONAL = {
    "na1": "americas",
    "br1": "americas",
    "la1": "americas",
    "la2": "americas",
    "euw1": "europe",
    "eun1": "europe",
    "tr1": "europe",
    "ru": "europe",
    "kr": "asia",
    "jp1": "asia",
    "oc1": "sea"
}

# ----------------------------
# Cached DDragon
# ----------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_ddragon_data():
    response = requests.get("https://ddragon.leagueoflegends.com/api/versions.json", timeout=10)
    response.raise_for_status()
    version = response.json()[0]

    item_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/item.json"
    item_response = requests.get(item_url, timeout=10)
    item_response.raise_for_status()

    return {
        "version": version,
        "items": item_response.json().get("data", {})
    }

ddragon_data = get_ddragon_data()

def champion_to_ddragon_name(champion_name: str) -> str:
    mapping = {
        "FiddleSticks": "Fiddlesticks",
        "MonkeyKing": "MonkeyKing",
        "KogMaw": "KogMaw",
        "KhaZix": "Khazix",
        "RekSai": "RekSai",
        "Belveth": "Belveth"
    }
    return mapping.get(champion_name, champion_name)

def get_champion_square_url(champion_name: str) -> str:
    champ = champion_to_ddragon_name(champion_name)
    return f"https://ddragon.leagueoflegends.com/cdn/{ddragon_data['version']}/img/champion/{champ}.png"

def get_item_icon_url(item_id: int) -> str:
    return f"https://ddragon.leagueoflegends.com/cdn/{ddragon_data['version']}/img/item/{item_id}.png"

def get_item_data():
    return ddragon_data["items"]

# ----------------------------
# Utility functions
# ----------------------------
def split_riot_id(full_input: str) -> tuple[str, str]:
    full_input = full_input.strip()
    if "#" in full_input:
        name, tag = full_input.split("#", 1)
        return name.strip(), tag.strip()
    return full_input, ""

def parse_csv_text(text: str) -> list[str]:
    return [x.strip() for x in text.split(",") if x.strip()]

def classify_match_type(queue_id: int, game_mode: str) -> str:
    if queue_id == 420:
        return "Ranked Solo"
    if queue_id == 440:
        return "Ranked Flex"
    if queue_id == 450 or game_mode == "ARAM":
        return "ARAM"
    if queue_id in [400, 430]:
        return "Normals"
    return "Other"

def normalize_role(role_value: str) -> str:
    if not role_value:
        return "UNKNOWN"
    role_value = role_value.upper()
    valid_roles = {"TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"}
    return role_value if role_value in valid_roles else "UNKNOWN"

def display_role_name(role_value: str) -> str:
    return {
        "TOP": "Top",
        "JUNGLE": "Jungle",
        "MIDDLE": "Mid",
        "BOTTOM": "ADC",
        "UTILITY": "Support",
        "UNKNOWN": "Unknown"
    }.get(role_value, role_value)

def format_rank(entry: Optional[Dict[str, Any]]) -> str:
    if not entry:
        return "Unavailable"
    return f'{entry.get("tier", "")} {entry.get("rank", "")} • {entry.get("leaguePoints", 0)} LP'

# ----------------------------
# Riot API helper with 429 retry/backoff
# ----------------------------
def riot_api_get(url: str, timeout: int = 20, max_retries: int = 3):
    for attempt in range(max_retries + 1):
        response = requests.get(url, headers=headers, timeout=timeout)

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            wait_seconds = float(retry_after) if retry_after else min(2 ** attempt, 8)
            if attempt < max_retries:
                time.sleep(wait_seconds)
                continue
            raise requests.exceptions.RequestException(
                f"Rate limited by Riot API (429). Retry after {wait_seconds} seconds."
            )

        if response.status_code >= 400:
            raise requests.exceptions.RequestException(
                f"Riot API error {response.status_code}: {url}"
            )

        return response

    raise requests.exceptions.RequestException("Riot API request failed after retries.")

# ----------------------------
# Riot account lookup
# ----------------------------
@st.cache_data(ttl=300, show_spinner=False)
def fetch_account_by_riot_id(game_name: str, tag_line: str, regional_region: str) -> dict:
    url = (
        f"https://{regional_region}.api.riotgames.com/riot/account/v1/accounts/"
        f"by-riot-id/{game_name}/{tag_line}"
    )
    return riot_api_get(url).json()

@st.cache_data(ttl=300, show_spinner=False)
def fetch_summoner_and_league(puuid: str, platform_region: str):
    summoner_url = (
        f"https://{platform_region}.api.riotgames.com/lol/summoner/v4/"
        f"summoners/by-puuid/{puuid}"
    )
    summoner_data = riot_api_get(summoner_url).json()

    solo_entry = None
    flex_entry = None

    summoner_id = summoner_data.get("id")
    if summoner_id:
        league_url = (
            f"https://{platform_region}.api.riotgames.com/lol/league/v4/"
            f"entries/by-summoner/{summoner_id}"
        )
        league_entries = riot_api_get(league_url).json()

        if isinstance(league_entries, list):
            solo_entry = next(
                (e for e in league_entries if e.get("queueType") == "RANKED_SOLO_5x5"),
                None
            )
            flex_entry = next(
                (e for e in league_entries if e.get("queueType") == "RANKED_FLEX_SR"),
                None
            )

    return summoner_data, solo_entry, flex_entry

# ----------------------------
# Fetch raw matches once, filter locally
# ----------------------------
@st.cache_data(ttl=300, show_spinner=False)
def fetch_raw_matches(
    puuid: str,
    platform_region: str,
    regional_region: str,
    count: int
):
    _, solo_entry, flex_entry = fetch_summoner_and_league(puuid, platform_region)

    collected_rows = []
    start = 0
    chunk_size = 20
    max_scan = 100

    while len(collected_rows) < count and start < max_scan:
        ids_url = (
            f"https://{regional_region}.api.riotgames.com/lol/match/v5/matches/"
            f"by-puuid/{puuid}/ids?start={start}&count={chunk_size}"
        )
        match_ids = riot_api_get(ids_url).json()

        if not match_ids:
            break

        for match_id in match_ids:
            if len(collected_rows) >= count:
                break

            match_url = (
                f"https://{regional_region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
            )

            try:
                match_data = riot_api_get(match_url).json()
                info = match_data.get("info", {})
                participants = info.get("participants", [])

                player_data = next((p for p in participants if p.get("puuid") == puuid), None)
                if not player_data:
                    continue

                queue_id = info.get("queueId", -1)
                game_mode = info.get("gameMode", "Unknown")
                match_type_check = classify_match_type(queue_id, game_mode)

                role_raw = normalize_role(player_data.get("teamPosition", "UNKNOWN"))
                role_display = display_role_name(role_raw)

                kills = int(player_data.get("kills", 0))
                deaths = int(player_data.get("deaths", 0))
                assists = int(player_data.get("assists", 0))
                cs_total = int(player_data.get("totalMinionsKilled", 0)) + int(
                    player_data.get("neutralMinionsKilled", 0)
                )
                duration_seconds = int(info.get("gameDuration", 0))
                duration_min = round(duration_seconds / 60, 1) if duration_seconds > 0 else 0.0
                cs_per_min = round(cs_total / duration_min, 2) if duration_min > 0 else 0.0
                items = [int(player_data.get(f"item{i}", 0)) for i in range(6)]

                collected_rows.append({
                    "match_id": match_id,
                    "game_creation": int(info.get("gameCreation", 0)),
                    "champion": player_data.get("championName", "Unknown"),
                    "role": role_display,
                    "match_type": match_type_check,
                    "win": bool(player_data.get("win", False)),
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists,
                    "kda": round((kills + assists) / max(1, deaths), 2),
                    "cs_total": cs_total,
                    "cs_per_min": cs_per_min,
                    "vision_score": int(player_data.get("visionScore", 0)),
                    "queue_id": queue_id,
                    "game_duration_min": duration_min,
                    "items": items,
                })

            except requests.exceptions.RequestException:
                continue

            time.sleep(0.12)

        start += chunk_size

    df = pd.DataFrame(collected_rows)
    if not df.empty:
        df = df.sort_values("game_creation", ascending=False).reset_index(drop=True)

    return df, solo_entry, flex_entry

def apply_local_filters(df: pd.DataFrame, match_type: str, role: str) -> pd.DataFrame:
    filtered = df.copy()

    if match_type != "All":
        filtered = filtered[filtered["match_type"] == match_type]

    if role != "All":
        filtered = filtered[filtered["role"] == role]

    return filtered.reset_index(drop=True)

# ----------------------------
# Analysis helpers
# ----------------------------
def compute_recent_form(filtered_df: pd.DataFrame, champion_name: str) -> float:
    champ_games = (
        filtered_df[filtered_df["champion"] == champion_name]
        .sort_values("game_creation", ascending=False)
        .head(5)
    )

    if champ_games.empty:
        return 0.0

    recent_wr = champ_games["win"].mean() * 100
    recent_kda = champ_games["kda"].mean()
    return (recent_wr * 0.7) + (min(recent_kda, 8) / 8 * 30)

def build_tiers(champion_summary: pd.DataFrame, filtered_df: pd.DataFrame) -> pd.DataFrame:
    if champion_summary.empty:
        return champion_summary

    max_games = champion_summary["games"].max() or 1
    max_kda = champion_summary["avg_kda"].max() or 1

    def compute_score(row):
        recent_form = compute_recent_form(filtered_df, row["champion"])
        norm_games = (row["games"] / max_games) * 100
        norm_kda = (row["avg_kda"] / max_kda) * 100
        return round(
            row["win_rate"] * 0.45 +
            norm_games * 0.25 +
            norm_kda * 0.20 +
            recent_form * 0.10,
            1
        )

    champion_summary = champion_summary.copy()
    champion_summary["tier_score"] = champion_summary.apply(compute_score, axis=1)
    champion_summary["tier"] = pd.cut(
        champion_summary["tier_score"],
        bins=[0, 58, 68, 78, 100],
        labels=["C", "B", "A", "S"],
        include_lowest=True
    ).astype(str)

    return champion_summary.sort_values(
        ["tier_score", "games"],
        ascending=[False, False]
    ).reset_index(drop=True)

# ----------------------------
# Simple match renderer
# ----------------------------
def render_recent_match_rows(filtered_df: pd.DataFrame):
    if filtered_df.empty:
        st.info("No recent matches for this filter.")
        return

    for _, match in filtered_df.iterrows():
        result = "Win" if match["win"] else "Loss"
        kda_line = f'{match["kills"]}/{match["deaths"]}/{match["assists"]}'
        st.markdown(
            f"""
            <div class="metric-card" style="margin-bottom: 0.6rem;">
                <div style="font-size:1.02rem;font-weight:700;">{match["champion"]} • {result}</div>
                <div style="color:#cbd5e1;font-size:0.92rem;">
                    {match["role"]} • {match["match_type"]} • KDA {kda_line} • {match["kda"]} KDA • {match["cs_per_min"]} CS/min
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ----------------------------
# Header
# ----------------------------
logo_path = Path("outdraft_logo.png")
logo_exists = logo_path.exists()

st.markdown('<div class="hero-card">', unsafe_allow_html=True)

if logo_exists:
    c1, c2, c3 = st.columns([1, 2.0, 1])
    with c2:
        st.markdown('<div class="logo-backdrop">', unsafe_allow_html=True)
        st.image(str(logo_path), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.title("Outdraft")

st.markdown(
    '<div class="hero-subtitle">Built to reduce draft anxiety and surface your smartest picks fast.</div>',
    unsafe_allow_html=True
)

search_col1, search_col2, search_col3, search_col4, search_col5 = st.columns([2.2, 1.0, 1.1, 0.8, 0.8])

with search_col1:
    riot_id_input = st.text_input("Riot ID", "HE TAKE ME#OHNO")
with search_col2:
    region_label = st.selectbox("Region", list(PLATFORM_OPTIONS.keys()), index=0)
with search_col3:
    queue_under_logo = st.selectbox("Queue / Match Type", ["All", "Ranked Solo", "Ranked Flex", "Normals", "ARAM"])
with search_col4:
    analyze_clicked = st.button("Analyze", use_container_width=True, type="primary")
with search_col5:
    refresh_clicked = st.button("Refresh", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

platform_region = PLATFORM_OPTIONS[region_label]
regional_region = PLATFORM_TO_REGIONAL[platform_region]

# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.header("Filters")
    role_filter = st.selectbox("Role", ["All", "Top", "Jungle", "Mid", "ADC", "Support"])
    st.markdown("---")
    st.subheader("Picks Context")
    ally_picks = parse_csv_text(st.text_input("Ally picks", ""))
    enemy_picks = parse_csv_text(st.text_input("Enemy picks", ""))
    bans = parse_csv_text(st.text_input("Bans", ""))

# ----------------------------
# Main logic
# ----------------------------
game_name, tag_line = split_riot_id(riot_id_input)
match_type_filter = queue_under_logo

if "games_to_show" not in st.session_state:
    st.session_state.games_to_show = 20

if "last_identity_key" not in st.session_state:
    st.session_state.last_identity_key = ""

identity_key = f"{game_name}|{tag_line}|{platform_region}"
trigger_analysis = analyze_clicked or refresh_clicked or (identity_key != st.session_state.last_identity_key)

if trigger_analysis:
    if not game_name or not tag_line:
        st.error("Please enter a Riot ID like Name#TAG.")
        st.stop()

    if refresh_clicked:
        st.cache_data.clear()

    st.session_state.last_identity_key = identity_key

    with st.spinner("Pulling Riot data..."):
        try:
            account_data = fetch_account_by_riot_id(game_name, tag_line, regional_region)
            puuid = account_data.get("puuid")

            if not puuid:
                st.error("Could not resolve that Riot ID to a PUUID.")
                st.stop()

            raw_df, solo_entry, flex_entry = fetch_raw_matches(
                puuid=puuid,
                platform_region=platform_region,
                regional_region=regional_region,
                count=st.session_state.games_to_show
            )

            if raw_df.empty:
                st.warning("No matches found.")
                st.stop()

            st.session_state.raw_df = raw_df
            st.session_state.solo_entry = solo_entry
            st.session_state.flex_entry = flex_entry

        except requests.exceptions.RequestException as e:
            msg = str(e)
            if "429" in msg:
                st.warning("Riot API rate limit hit. Wait a few seconds and try again.")
            else:
                st.error(f"API Error: {e}")
            st.stop()
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

if "raw_df" in st.session_state:
    filtered_df = apply_local_filters(
        st.session_state.raw_df,
        match_type=match_type_filter,
        role=role_filter
    )

    solo_entry = st.session_state.get("solo_entry")
    flex_entry = st.session_state.get("flex_entry")

    if filtered_df.empty:
        st.warning("No matches found for that filter.")
        st.stop()

    champion_summary = (
        filtered_df.groupby("champion")
        .agg(
            games=("champion", "count"),
            wins=("win", "sum"),
            avg_kda=("kda", "mean"),
            avg_cs_per_min=("cs_per_min", "mean")
        )
        .reset_index()
    )

    champion_summary["win_rate"] = (
        champion_summary["wins"] / champion_summary["games"] * 100
    ).round(1)

    champion_summary["avg_kda"] = champion_summary["avg_kda"].round(2)
    champion_summary["avg_cs_per_min"] = champion_summary["avg_cs_per_min"].round(2)

    tier_df = build_tiers(champion_summary, filtered_df)

    total_games = len(filtered_df)
    total_wins = int(filtered_df["win"].sum())
    overall_winrate = round((total_wins / total_games) * 100, 1)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Games", total_games)
    with col2:
        st.metric("Win Rate", f"{overall_winrate}%")
    with col3:
        st.metric("Solo Rank", format_rank(solo_entry))
    with col4:
        st.metric("Flex Rank", format_rank(flex_entry))

    tab1, tab2 = st.tabs(["Overview", "Recent Matches"])

    with tab1:
        st.subheader("Champion Summary")
        st.dataframe(
            tier_df[
                [
                    "champion",
                    "games",
                    "wins",
                    "win_rate",
                    "avg_kda",
                    "avg_cs_per_min",
                    "tier",
                    "tier_score"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.subheader("Recent Matches")
        render_recent_match_rows(filtered_df.head(20))

else:
    st.info("Enter Riot ID and click Analyze.")
