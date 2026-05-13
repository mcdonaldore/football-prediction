from flask import Flask, render_template, request, jsonify
import pandas as pd
from scipy.stats import poisson
import requests

app = Flask(__name__)

# =========================
# CONFIG (LIVE API)
# =========================
API_KEY = "8ffd9736183cc334c93b541o867ea1a3"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

# =========================
# LOAD CSV DATA
# =========================
data = pd.read_csv("results.csv")

teams = pd.concat([data['home_team'], data['away_team']]).unique()

team_stats = {}

for team in teams:

    home = data[data['home_team'] == team]
    away = data[data['away_team'] == team]

    goals_scored = home['home_score'].sum() + away['away_score'].sum()
    goals_conceded = home['away_score'].sum() + away['home_score'].sum()

    matches = len(home) + len(away)

    if matches == 0:
        continue

    attack = goals_scored / matches
    defense = goals_conceded / matches

    team_stats[team] = {
        "attack": attack,
        "defense": defense
    }

# =========================
# LIVE API FUNCTION
# =========================
def get_live_team_stats(team_name):

    url = f"{BASE_URL}/teams?search={team_name}"
    res = requests.get(url, headers=HEADERS).json()

    if not res["response"]:
        return None

    team_id = res["response"][0]["team"]["id"]

    url = f"{BASE_URL}/fixtures?team={team_id}&last=10"
    res = requests.get(url, headers=HEADERS).json()

    matches = res.get("response", [])

    goals_scored = 0
    goals_conceded = 0

    if len(matches) == 0:
        return None

    for match in matches:
        home_goals = match["goals"]["home"] or 0
        away_goals = match["goals"]["away"] or 0

        if match["teams"]["home"]["id"] == team_id:
            goals_scored += home_goals
            goals_conceded += away_goals
        else:
            goals_scored += away_goals
            goals_conceded += home_goals

    return {
        "attack": goals_scored / len(matches),
        "defense": goals_conceded / len(matches)
    }

# =========================
# HOME ROUTE
# =========================
@app.route("/")
def home():
    return render_template("index.html", teams=sorted(teams))

# =========================
# PREDICTION ROUTE
# =========================
@app.route("/predict", methods=["POST"])
def predict():

    req = request.get_json()
    home_team = req["home"]
    away_team = req["away"]

    home_stats = team_stats.get(home_team)
    away_stats = team_stats.get(away_team)

    # fallback to live API
    if not home_stats:
        home_stats = get_live_team_stats(home_team)

    if not away_stats:
        away_stats = get_live_team_stats(away_team)

    if not home_stats or not away_stats:
        return jsonify({"error": "Team data not available"}), 400

    home_xg = home_stats["attack"] * away_stats["defense"]
    away_xg = away_stats["attack"] * home_stats["defense"]

    home_prob = poisson.pmf(2, home_xg) * 100
    away_prob = poisson.pmf(2, away_xg) * 100

    draw_prob = 100 - home_prob - away_prob

    if home_prob > away_prob:
        prediction = f"{home_team} likely to win"
    elif away_prob > home_prob:
        prediction = f"{away_team} likely to win"
    else:
        prediction = "Draw likely"

    return jsonify({
        "home_xg": round(home_xg, 2),
        "away_xg": round(away_xg, 2),
        "home_prob": round(home_prob, 2),
        "away_prob": round(away_prob, 2),
        "draw_prob": round(draw_prob, 2),
        "prediction": prediction
    })

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)