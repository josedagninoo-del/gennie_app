import streamlit as st
import requests
from datetime import datetime
import os

# -----------------------
# KEYS
# -----------------------
API_KEY = st.secrets.get("API_KEY")
ODDS_KEY = st.secrets.get("ODDS_KEY")

# -----------------------
# FETCH MATCHES (REAL)
# -----------------------
def fetch_matches():
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    today = datetime.now().strftime("%Y-%m-%d")

    res = requests.get(url, headers=headers, params={"date": today})
    data = res.json()

    matches = []

    if "response" not in data:
        return []

    for m in data["response"]:
        matches.append({
            "home": m["teams"]["home"]["name"],
            "away": m["teams"]["away"]["name"],
            "league": m["league"]["name"],
            "kickoff": m["fixture"]["date"]
        })

    return matches

# -----------------------
# FETCH ODDS (REAL PRO)
# -----------------------
def fetch_odds():
    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?apiKey={ODDS_KEY}&regions=eu&markets=h2h"

    try:
        res = requests.get(url)
        data = res.json()

        odds_dict = {}

        for game in data:
            key = f"{game['home_team']} vs {game['away_team']}"

            odds_dict[key] = {
                "home": game["bookmakers"][0]["markets"][0]["outcomes"][0]["price"],
                "away": game["bookmakers"][0]["markets"][0]["outcomes"][1]["price"]
            }

        return odds_dict

    except:
        return {}

# -----------------------
# GENIE ENGINE PRO
# -----------------------
def classify(home, away):
    attack = ["Liverpool", "Leverkusen", "Atalanta", "Brighton", "Fiorentina"]
    defense = ["Getafe", "Torino", "Strasbourg"]

    if any(t in home for t in attack) or any(t in away for t in attack):
        return "HIGH TEMPO"
    elif any(t in home for t in defense) and any(t in away for t in defense):
        return "LOW BLOCK"
    else:
        return "BALANCED"

def analyze(match, odds):
    game_type = classify(match["home"], match["away"])

    base_score = {
        "HIGH TEMPO": 8,
        "BALANCED": 6,
        "LOW BLOCK": 4
    }[game_type]

    # ajuste por cuotas
    if odds:
        base_score += 1

    return {
        "type": game_type,
        "confidence": base_score,
        "strategy": {
            "HIGH TEMPO": "Lay Under / Over trading",
            "BALANCED": "Momentum Match Odds",
            "LOW BLOCK": "Wait / Draw"
        }[game_type],
        "prophecy": f"Partido {game_type} con comportamiento condicionado por ritmo y primer gol."
    }

# -----------------------
# UI
# -----------------------
st.title("🔥 GENIE PRO REAL")

matches = fetch_matches()
odds_data = fetch_odds()

data = []

for m in matches:
    key = f"{m['home']} vs {m['away']}"
    odds = odds_data.get(key)

    analysis = analyze(m, odds)

    data.append({
        "match": key,
        "analysis": analysis,
        "odds": odds,
        "raw": m
    })

# ranking real
ranked = sorted(data, key=lambda x: x["analysis"]["confidence"], reverse=True)

st.markdown("## 🏆 TOP REAL")
for i, r in enumerate(ranked[:5]):
    st.write(f"{i+1}. {r['match']} → {r['analysis']['confidence']}")

# selector
selected = st.selectbox("Selecciona partido", [d["match"] for d in data])

sel = next(d for d in data if d["match"] == selected)

st.subheader(selected)
st.write(sel["raw"]["league"])
st.write(sel["raw"]["kickoff"])

st.markdown("### Odds")
st.write(sel["odds"] if sel["odds"] else "No odds")

st.markdown("### Analysis")
st.write(sel["analysis"]["prophecy"])

st.markdown("### Strategy")
st.write(sel["analysis"]["strategy"])

st.markdown("### Confidence")
st.write(sel["analysis"]["confidence"])
