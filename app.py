import streamlit as st
import requests

st.set_page_config(page_title="Riot API Test", layout="wide")
st.title("Riot API Test")

# This pulls your key from Streamlit secrets
api_key = st.secrets["RIOT_API_KEY"]

game_name = st.text_input("Riot ID name", "Doublelift")
tag_line = st.text_input("Riot ID tag", "NA1")

if st.button("Test Riot API"):
    headers = {
        "X-Riot-Token": api_key
    }

    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"

    response = requests.get(url, headers=headers)

    st.write("Status code:", response.status_code)

    try:
        st.json(response.json())
    except Exception:
        st.write(response.text)
