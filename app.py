import streamlit as st
import requests
import pandas as pd
from pathlib import Path
import time

st.set_page_config(
    page_title="Outdraft",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# Core config
# ----------------------------
@st.cache_data(ttl=3600)
def get_headers():
    return {"X-Riot-Token": st.secrets["RIOT_API_KEY"]}

headers = get_headers()

PLATFORM_OPTIONS = {
    "NA": "na1", "EUW": "euw1", "EUNE": "eun1", "KR": "kr", "BR": "br1",
    "LAN": "la1", "LAS": "la2", "OCE": "oc1", "JP": "jp1", "TR": "tr1", "RU": "ru"
}

PLATFORM_TO_REGIONAL = {
    "na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas",
    "euw1": "europe", "eun1": "europe", "tr1": "europe", "ru": "europe",
    "kr": "asia", "jp1": "asia", "oc1": "sea"
}

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
    valid = {"TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"}
    return role_value if role_value in valid else "UNKNOWN"

def display_role_name(role_value: str) -> str:
    return {
        "TOP": "Top",
        "JUNGLE": "Jungle",
        "MIDDLE": "Mid",
        "BOTTOM": "ADC",
        "UTILITY": "Support",
        "UNKNOWN": "Unknown",
    }.get(role_value, role_value)

def format_rank(entry) -> str:
    if not entry:
        return "Unavailable"
    return f'{entry.get("tier", "")} {entry.get("rank", "")} • {entry.get("leaguePoints", 0)} LP'

def riot_api_get(url: str, timeout: int = 20):
    response = requests.get(url, headers=headers, timeout=timeout)
    if response.status_code == 429:
        raise requests.exceptions.RequestException("Rate limited by Riot API (429).")
    if response.status_code >= 400:
        raise requests.exceptions.RequestException(
            f"Riot API error {response.status_code}: {url}"
        )
    return response

# ----------------------------
# Riot account lookup
# ----------------------------
@st.cache_data(ttl=300, show_spinner=False)
def fetch_account_by_riot_id(game_name: str, tag_line: str, regional_region: str) -> dict:
    url = (
        f"https://{regional_region}.api.riotgames.com/riot/account/v1/accounts/"
        f"by-riot-id/{game_name}/{tag_line}"
    )
    response = riot_api_get(url)
    return response.json()

@st.cache_data(ttl=300, show_spinner=False)
def fetch_summoner_and_league(puuid: str, platform_region: str):
    summoner_url = (
        f"https://{platform_region}.api.riotgames.com/lol/summoner/v4/"
        f"summoners/by-puuid/{puuid}"
    )
    summoner_data = riot_api_get(summoner_url).json()

    solo_entry, flex_entry = None, None
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
# Match fetching
# ----------------------------
@st.cache_data(ttl=300, show_spinner=False)
def fetch_account_and_matches(
    puuid: str,
    platform_region: str,
    regional_region: str,
    match_type: str,
    role: str,
    count: int
):
    _, solo_entry, flex_entry = fetch_summoner_and_league(puuid, platform_region)

    collected_rows = []
    start = 0
    chunk_size = 100
    max_scan = 500

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

                if match_type != "All" and match_type_check != match_type:
                    continue

                role_raw = normalize_role(player_data.get("teamPosition", "UNKNOWN"))
                role_display = display_role_name(role_raw)

                if role != "All" and role_display != role:
                    continue

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

            time.sleep(0.05)

        start += chunk_size

    filtered_df = pd.DataFrame(collected_rows)

    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values("game_creation", ascending=False).reset_index(drop=True)

    return filtered_df, solo_entry, flex_entry

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
# UI
# ----------------------------
logo_path = Path("outdraft_logo.png")
logo_exists = logo_path.exists()

st.markdown('<div class="hero-card">', unsafe_allow_html=True)
if logo_exists:
    c1, c2, c3 = st.columns([1, 2.0, 1])
    with c2:
        st.image(str(logo_path), use_container_width=True)
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
    queue_under_logo = st.selectbox(
        "Queue / Match Type",
        ["All", "Ranked Solo", "Ranked Flex", "Normals", "ARAM"]
    )
with search_col4:
    analyze_clicked = st.button("Analyze", use_container_width=True, type="primary")
with search_col5:
    refresh_clicked = st.button("Refresh", use_container_width=True)

platform_region = PLATFORM_OPTIONS[region_label]
regional_region = PLATFORM_TO_REGIONAL[platform_region]

with st.sidebar:
    st.header("Filters")
    role_filter = st.selectbox("Role", ["All", "Top", "Jungle", "Mid", "ADC", "Support"])
    st.markdown("---")
    st.subheader("Picks Context")
    ally_picks = parse_csv_text(st.text_input("Ally picks", ""))
    enemy_picks = parse_csv_text(st.text_input("Enemy picks", ""))
    bans = parse_csv_text(st.text_input("Bans", ""))

game_name, tag_line = split_riot_id(riot_id_input)
match_type_filter = queue_under_logo
filter_key = f"{game_name}|{tag_line}|{platform_region}|{match_type_filter}|{role_filter}"

if "current_filter_key" not in st.session_state:
    st.session_state.current_filter_key = ""
if "games_to_show" not in st.session_state:
    st.session_state.games_to_show = 20

trigger_analysis = analyze_clicked or refresh_clicked or (
    filter_key != st.session_state.current_filter_key
)

if trigger_analysis:
    if not game_name or not tag_line:
        st.error("Please enter a Riot ID like Name#TAG.")
        st.stop()

    st.session_state.current_filter_key = filter_key

    with st.spinner("Pulling Riot data..."):
        try:
            account_data = fetch_account_by_riot_id(game_name, tag_line, regional_region)
            puuid = account_data.get("puuid")

            if not puuid:
                st.error("Could not resolve that Riot ID to a PUUID.")
                st.stop()

            filtered_df, solo_entry, flex_entry = fetch_account_and_matches(
                puuid=puuid,
                platform_region=platform_region,
                regional_region=regional_region,
                match_type=match_type_filter,
                role=role_filter,
                count=st.session_state.games_to_show,
            )

            if filtered_df.empty:
                st.warning("No matches found for that filter.")
                st.stop()

            champion_summary = (
                filtered_df.groupby("champion")
                .agg(
                    games=("champion", "count"),
                    wins=("win", "sum"),
                    avg_kda=("kda", "mean"),
                    avg_cs_per_min=("cs_per_min", "mean"),
                )
                .reset_index()
            )

            champion_summary["win_rate"] = (
                champion_summary["wins"] / champion_summary["games"] * 100
            ).round(1)

            tier_df = build_tiers(champion_summary, filtered_df)

            total_games = len(filtered_df)
            total_wins = int(filtered_df["win"].sum())
            overall_winrate = round((total_wins / total_games) * 100, 1)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Games", total_games)
            col2.metric("Win Rate", f"{overall_winrate}%")
            col3.metric("Solo Rank", format_rank(solo_entry))
            col4.metric("Flex Rank", format_rank(flex_entry))

            st.subheader("Champion Summary")
            st.dataframe(
                tier_df[["champion", "games", "wins", "win_rate", "avg_kda", "avg_cs_per_min", "tier", "tier_score"]],
                use_container_width=True
            )

            st.subheader("Recent Matches")
            st.dataframe(
                filtered_df[["champion", "role", "match_type", "win", "kills", "deaths", "assists", "kda", "cs_per_min"]],
                use_container_width=True
            )

        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
        except Exception as e:
            st.error(f"Analysis failed: {e}")
else:
    st.info("Enter Riot ID and click Analyze.")
