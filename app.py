import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Riot Match Details Test", layout="wide")
st.title("Riot Match Details Test")

api_key = st.secrets["RIOT_API_KEY"]
headers = {"X-Riot-Token": api_key}

game_name = st.text_input("Riot ID name", "HE TAKE ME")
tag_line = st.text_input("Riot ID tag", "OHNO")

if st.button("Load Match Details"):
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

        matches_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=5"
        matches_response = requests.get(matches_url, headers=headers)

        st.write("Match list status code:", matches_response.status_code)

        if matches_response.status_code != 200:
            try:
                st.json(matches_response.json())
            except Exception:
                st.write(matches_response.text)
        else:
            match_ids = matches_response.json()
            st.subheader("Recent Match IDs")
            st.json(match_ids)

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

                rows.append({
                    "match_id": match_id,
                    "champion": player_data.get("championName"),
                    "role": player_data.get("teamPosition"),
                    "win": player_data.get("win"),
                    "kills": player_data.get("kills"),
                    "deaths": player_data.get("deaths"),
                    "assists": player_data.get("assists"),
                    "kda": round(
                        (player_data.get("kills", 0) + player_data.get("assists", 0)) /
                        max(1, player_data.get("deaths", 0)),
                        2
                    ),
                    "game_mode": info.get("gameMode"),
                    "game_duration_min": round(info.get("gameDuration", 0) / 60, 1)
                })

            if rows:
                df = pd.DataFrame(rows)
                st.subheader("Recent Match Details")
                st.dataframe(df, use_container_width=True)

                st.subheader("Quick Summary")
                st.write("Games analyzed:", len(df))
                st.write("Wins:", int(df["win"].sum()))
                st.write("Losses:", int((~df["win"]).sum()))
                st.write("Average KDA:", round(df["kda"].mean(), 2))

                champion_summary = (
                    df.groupby("champion")
                    .agg(
                        games=("champion", "count"),
                        avg_kda=("kda", "mean"),
                        wins=("win", "sum")
                    )
                    .reset_index()
                )
                champion_summary["win_rate"] = round((champion_summary["wins"] / champion_summary["games"]) * 100, 1)

                st.subheader("Champion Summary")
                st.dataframe(champion_summary.sort_values(by="games", ascending=False), use_container_width=True)
            else:
                st.warning("No match details could be loaded.")
