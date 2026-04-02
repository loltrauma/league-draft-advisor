import streamlit as st
import requests

st.set_page_config(page_title="Riot Match History Test", layout="wide")
st.title("Riot Match History Test")

api_key = st.secrets["RIOT_API_KEY"]
headers = {"X-Riot-Token": api_key}

game_name = st.text_input("Riot ID name", "HE TAKE ME")
tag_line = st.text_input("Riot ID tag", "OHNO")

if st.button("Load Match History"):
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

        st.write("PUUID found:")
        st.write(puuid)

        matches_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=10"
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
