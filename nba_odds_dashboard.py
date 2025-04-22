# nba_dashboard.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="NBA Advanced Odds & Analytics", layout="wide")
st.title("🏀 NBA Odds + Deep Analytics")
st.caption("Live odds + player/team breakdowns from public sources and sportsbooks")

# --- Tabs Layout ---
tab1, tab2, tab3 = st.tabs(["📊 Live Odds", "📈 Player Stats", "🤖 Predictive Analytics"])

# --- Tab 1: Live Odds from the-odds-api (merged with balldontlie) ---
with tab1:
    st.subheader("📊 Real-Time NBA Odds")
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"] if "ODDS_API_KEY" in st.secrets else "0c03cbe55c11b193e6d23407c48cc604"

    if not ODDS_API_KEY:
        st.warning("No Odds API key found. Add 'ODDS_API_KEY' to Streamlit secrets to enable odds fetching.")
    else:
        ODDS_ENDPOINT = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
        odds_params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "spreads,totals,h2h",
            "oddsFormat": "american",
            "bookmakers": "fanduel,draftkings,betmgm"
        }

        try:
            res = requests.get(ODDS_ENDPOINT, params=odds_params)

            # Fetch today's NBA games from balldontlie
            today = datetime.utcnow().strftime('%Y-%m-%d')
            balldontlie_games = []
            try:
                bdl_url = f"https://www.balldontlie.io/api/v1/games?start_date={today}&end_date={today}"
                bdl_res = requests.get(bdl_url)
                bdl_res.raise_for_status()
                balldontlie_games = bdl_res.json().get("data", [])
            except Exception as e:
                st.warning(f"Could not fetch today's games from balldontlie: {e}")
            res.raise_for_status()
            odds_data = res.json()

            if odds_data:
                # Cross-check Odds API data with balldontlie games
                game_matchups = []
                for game in odds_data:
                    for bdl_game in balldontlie_games:
                        if bdl_game['home_team']['full_name'] in game['home_team'] and \
                           bdl_game['visitor_team']['full_name'] in game['away_team']:
                            game_matchups.append(game)
                            break
                target_games = game_matchups if game_matchups else odds_data

                odds_rows = []
                for game in target_games:
                    matchup = f"{game['away_team']} @ {game['home_team']}"
                    start_time = datetime.fromisoformat(game['commence_time'].replace("Z", "+00:00"))
                    start_time_local = start_time.strftime('%Y-%m-%d %I:%M %p')
                    for book in game.get("bookmakers", []):
                        for market in book.get("markets", []):
                            for out in market.get("outcomes", []):
                                odds_rows.append({
                                    "Matchup": matchup,
                                    "Start Time": start_time_local,
                                    "Bookmaker": book['title'],
                                    "Market": market['key'],
                                    "Team": out['name'],
                                    "Point": out.get('point'),
                                    "Odds": out['price']
                                })

                df_odds = pd.DataFrame(odds_rows)
                matchups_today = df_odds['Matchup'].unique()
                selected_matchup = st.selectbox("Select a matchup to highlight:", matchups_today)
                st.dataframe(df_odds[df_odds['Matchup'] == selected_matchup].sort_values(by="Bookmaker"))
                st.dataframe(df_odds[df_odds['Matchup'] == selected_matchup].sort_values(by="Bookmaker"))
            else:
                st.warning("No odds available right now.")
        except Exception as e:
            st.error(f"Failed to load odds: {e}")

# --- Tab 2: NBA Player Stats ---
with tab2:
    st.subheader("📈 NBA Player Performance Tracker")
    BALDONTLIE_API = "https://www.balldontlie.io/api/v1/players"

    player_query = st.text_input("Search NBA Player:", "Stephen Curry")
    if player_query:
        try:
            res = requests.get(BALDONTLIE_API, params={"search": player_query})
            res.raise_for_status()
            player_data = res.json().get("data", [])
            if player_data:
                st.json(player_data[0])
            else:
                st.warning("No player found.")
        except Exception as e:
            st.error(f"Error loading player stats: {e}")

# --- Tab 3: Predictive Analytics ---
with tab3:
    st.subheader("🤖 Smart Betting Indicators")
    st.caption("This section will generate performance probabilities using scraped data.")
    st.markdown("- Expected points vs line 📉")
    st.markdown("- Value bet detection 🔎")
    st.markdown("- Outlier stats, streaks, rest days impact, etc.")

    st.info("We will use external stats (e.g. from ESPN, NBA.com, Basketball Reference)")
