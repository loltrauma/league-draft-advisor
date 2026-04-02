import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="LoL Player Analyzer", layout="wide")
st.title("LoL Player Analyzer")

api_key = st.secrets["RIOT_API_KEY"]
headers = {"X-Riot-Token": api_key}

game_name = st.text_input("Riot ID name", "HE TAKE ME")
tag_line = st.text_input("Riot ID tag", "OHNO")
match_count = st.slider("How many recent matches to analyze?", 5, 20, 10)

if st.button("Analyze Player"):
    account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    account_response = requests.get(account_url, headers=headers)

    st.write("Account status code:", account_response.status_code)

    if account_response.status_code != 200:
        try:
            st.json(account_response.json())
        except Exception:
            st.write(account_response.text)
    else:
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
        else:
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

                deaths = player_data.get("deaths", 0)
                kills = player_data.get("kills", 0)
                assists = player_data.get("assists", 0)

                rows.append({
                    "match_id": match_id,
                    "champion": player_data.get("championName"),
                    "role": player_data.get("teamPosition"),
                    "win": player_data.get("win"),
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists,
                    "kda": round((kills + assists) / max(1, deaths), 2),
                    "cs": player_data.get("totalMinionsKilled", 0) + player_data.get("neutralMinionsKilled", 0),
                    "vision_score": player_data.get("visionScore", 0),
                    "damage_to_champs": player_data.get("totalDamageDealtToChampions", 0),
                    "game_mode": info.get("gameMode"),
                    "game_duration_min": round(info.get("gameDuration", 0) / 60, 1)
                })

            if not rows:
                st.warning("No match details could be loaded.")
            else:
                df = pd.DataFrame(rows)

                st.subheader("Recent Match Details")
                st.dataframe(df, use_container_width=True)

                st.subheader("Quick Summary")
                total_games = len(df)
                total_wins = int(df["win"].sum())
                total_losses = total_games - total_wins
                overall_winrate = round((total_wins / total_games) * 100, 1)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Games", total_games)
                col2.metric("Wins", total_wins)
                col3.metric("Losses", total_losses)
                col4.metric("Win Rate", f"{overall_winrate}%")

                col5, col6, col7 = st.columns(3)
                col5.metric("Avg KDA", round(df["kda"].mean(), 2))
                col6.metric("Avg CS", round(df["cs"].mean(), 1))
                col7.metric("Avg Damage", int(df["damage_to_champs"].mean()))

                champion_summary = (
                    df.groupby("champion")
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

                st.subheader("Champion Summary")
                st.dataframe(
                    champion_summary.sort_values(by=["games", "win_rate"], ascending=[False, False]),
                    use_container_width=True
                )

                st.subheader("Role Summary")
                st.dataframe(
                    role_summary.sort_values(by="games", ascending=False),
                    use_container_width=True
                )
