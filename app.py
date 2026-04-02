import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class TeamState:
    blue_picks: List[str]
    red_picks: List[str]
    blue_bans: List[str]
    red_bans: List[str]
    blue_side: bool = True

class LOLChampionAnalyzer:
    def __init__(self):
        self.roles = ["top", "jungle", "mid", "adc", "support"]
        self.all_champions = [
            "Aatrox","Ahri","Akali","Alistar","Amumu","Annie","Ashe","Azir",
            "Blitzcrank","Brand","Braum","Caitlyn","Camille","Cassiopeia",
            "Darius","Diana","Draven","Ekko","Elise","Evelynn","Ezreal",
            "Fiora","Fizz","Galio","Garen","Gragas","Graves","Gwen",
            "Hecarim","Irelia","Janna","JarvanIV","Jax","Jayce","Jhin",
            "Jinx","Kaisa","Karma","Karthus","Kassadin","Katarina",
            "Kayle","Kayn","Kennen","KhaZix","Kindred","LeBlanc",
            "LeeSin","Leona","Lillia","Lissandra","Lucian","Lulu",
            "Lux","Malphite","Malzahar","Maokai","MasterYi",
            "Mordekaiser","Morgana","Nami","Nasus","Nautilus",
            "Neeko","Nidalee","Nocturne","Olaf","Orianna","Ornn",
            "Pantheon","Poppy","Pyke","Qiyana","Rakan","Rammus",
            "Renekton","Riven","Ryze","Samira","Sejuani","Senna",
            "Sett","Shaco","Shen","Sion","Sivir","Soraka","Swain",
            "Sylas","Syndra","TahmKench","Talon","Teemo","Thresh",
            "Tristana","Trundle","Tryndamere","TwistedFate",
            "Twitch","Udyr","Urgot","Varus","Vayne","Veigar",
            "Vi","Viktor","Vladimir","Volibear","Warwick","Wukong",
            "Xayah","Xerath","Yasuo","Yone","Zed","Zeri","Ziggs","Zyra"
        ]

    def calculate_score(self, champion: str) -> float:
        return np.random.uniform(50, 80)

    def get_recommendations(self, role: str, team_state: TeamState) -> List[Tuple[str, float]]:
        scores = []
        for champ in self.all_champions:
            score = self.calculate_score(champ)
            scores.append((champ, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:10]

def main():
    st.title("🏆 League of Legends Champion Recommender")

    analyzer = LOLChampionAnalyzer()

    st.sidebar.header("Game State")

    blue_side = st.sidebar.checkbox("Blue Side", value=True)

    blue_picks = st.sidebar.text_input("Blue Picks (comma separated)").split(",")
    red_picks = st.sidebar.text_input("Red Picks (comma separated)").split(",")
    blue_bans = st.sidebar.text_input("Blue Bans").split(",")
    red_bans = st.sidebar.text_input("Red Bans").split(",")

    team_state = TeamState(
        blue_picks=[p.strip() for p in blue_picks if p.strip()],
        red_picks=[p.strip() for p in red_picks if p.strip()],
        blue_bans=[b.strip() for b in blue_bans if b.strip()],
        red_bans=[r.strip() for r in red_bans if r.strip()],
        blue_side=blue_side
    )

    role = st.selectbox("Select role", ["top","jungle","mid","adc","support"])

    if st.button("Get Recommendations"):
        recs = analyzer.get_recommendations(role, team_state)
        for champ, score in recs:
            st.write(f"{champ}: {score:.2f}")

if __name__ == "__main__":
    main()