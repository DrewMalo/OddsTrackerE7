# nba_odds_tracker.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt

# --- Title/Header ---
st.set_page_config(page_title="NBA Odds Tracker", layout="wide")
st.title("NBA Odds Tracker \U0001F3C0")
st.caption("Real-time NBA lines: Moneylines, Spreads, Totals & Player Props from FanDuel, DraftKings, and BetMGM")

# --- API Setup ---
API_KEY = '0c03cbe55c11b193e6d23407c48cc604'
API_URL = 'https://api.the-odds-api.com/v4/sports/basketball_nba/odds'
API_EVENT_URL = 'https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/markets'
params = {
    'apiKey': API_KEY,
    'regions': 'us',
    'markets': 'h2h,spreads,totals',
    'oddsFormat': 'american',
    'bookmakers': 'fanduel,draftkings,betmgm'
}

@st.cache_data(ttl=60)
def fetch_odds():
    response = requests.get(API_URL, params=params)
    if response.status_code != 200:
        st.error(f"Failed to load odds: {response.status_code} - {response.text}")
        return []
    st.caption(f"Requests remaining: {response.headers.get('x-requests-remaining')}, Used: {response.headers.get('x-requests-used')}")
    return response.json()

@st.cache_data(ttl=60)
def fetch_player_props(event_id):
    url = API_EVENT_URL.format(event_id=event_id)
    response = requests.get(url, params={'apiKey': API_KEY, 'markets': 'player_points', 'oddsFormat': 'american'})
    if response.status_code != 200:
        return []
    return response.json()

# --- Helper ---
def implied_prob(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return -odds / (-odds + 100)

# --- Data Processing ---
odds_data = fetch_odds()
games, props = [], []
for game in odds_data:
    matchup = f"{game['away_team']} @ {game['home_team']}"
    start_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M UTC')
    row = {'Timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'Matchup': matchup, 'Start Time': start_time}

    for bookmaker in game['bookmakers']:
        book = bookmaker['title']
        for market in bookmaker['markets']:
            market_key = market['key']
            for outcome in market['outcomes']:
                if market_key == 'h2h':
                    team = outcome['name']
                    row[f"{book} ML - {team}"] = outcome['price']
                    row[f"{book} % - {team}"] = round(implied_prob(outcome['price']) * 100, 1)
                elif market_key == 'spreads':
                    team = outcome['name']
                    row[f"{book} Spread - {team}"] = f"{outcome['point']} ({outcome['price']})"
                elif market_key == 'totals':
                    label = 'Over' if 'Over' in outcome['name'] else 'Under'
                    row[f"{book} Total - {label}"] = f"{outcome['point']} ({outcome['price']})"

    try:
        player_markets = fetch_player_props(game['id'])
        for market in player_markets:
            if market['key'] == 'player_points':
                for bookmaker in market.get('bookmakers', []):
                    book = bookmaker['title']
                    for outcome in bookmaker.get('outcomes', []):
                        props.append({
                            'Timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                            'Matchup': matchup,
                            'Start Time': start_time,
                            'Team': game['home_team'] if outcome['name'] in game['home_team'] else game['away_team'],
                            'Bookmaker': book,
                            'Player': outcome['name'],
                            'Prop': 'Points',
                            'Line': outcome.get('point'),
                            'Odds': outcome.get('price')
                        })
    except Exception as e:
        st.warning(f"Failed to load props for game: {matchup}")

    games.append(row)

# --- DataFrames ---
df = pd.DataFrame(games)
df_props = pd.DataFrame(props)

# --- Save to CSV (disabled for Streamlit Cloud) ---
csv_file = 'nba_odds_history.csv'
# Disabled CSV saving for deployment compatibility

# --- Tabs Layout ---
tab1, tab2, tab3 = st.tabs(["\U0001F4CA Game Odds", "\U0001F4C8 Line Movement", "\U0001F3AF Player Props"])

with tab1:
    st.subheader("\U0001F4CA Game Odds: Moneylines, Spreads, Totals")
    def highlight_best(row):
        styles = [''] * len(row)
        ml_cols = [col for col in df.columns if 'ML -' in col]
        teams = set(col.split(' - ')[1] for col in ml_cols)
        for team in teams:
            team_cols = [col for col in ml_cols if col.endswith(team)]
            best_col = max(team_cols, key=lambda col: row[col] if pd.notna(row[col]) else -9999)
            styles[df.columns.get_loc(best_col)] = 'background-color: lightgreen'
        return styles
    df_display = df.style.apply(highlight_best, axis=1)
    st.dataframe(df_display, use_container_width=True)

with tab2:
    st.subheader("\U0001F4C8 Moneyline Line Movement")
    if os.path.exists(csv_file):
        history_df = pd.read_csv(csv_file)
        matchups = history_df['Matchup'].unique()
        selected_matchup = st.selectbox("Choose a matchup to analyze:", matchups)
        selected_team = st.selectbox("Choose team odds to track:", [col.split(' - ')[1] for col in history_df.columns if 'ML -' in col])
        selected_book = st.selectbox("Choose a sportsbook:", ['FanDuel', 'DraftKings', 'BetMGM'])
        odds_col = f"{selected_book} ML - {selected_team}"
        chart_data = history_df[history_df['Matchup'] == selected_matchup][['Timestamp', odds_col]].dropna()
        chart_data['Timestamp'] = pd.to_datetime(chart_data['Timestamp'])
        st.line_chart(chart_data.set_index('Timestamp'))
    else:
        st.info("Line movement data is not being stored in cloud mode.")

with tab3:
    st.subheader("\U0001F3AF Player Points Props by Team")
    if not df_props.empty:
        selected_team = st.selectbox("Select a team:", sorted(df_props['Team'].dropna().unique()))
        filtered = df_props[df_props['Team'] == selected_team]
        selected_player = st.selectbox("Filter by player (optional):", ["All"] + sorted(filtered['Player'].dropna().unique()))
        if selected_player != "All":
            st.dataframe(filtered[filtered['Player'] == selected_player], use_container_width=True)
        else:
            st.dataframe(filtered, use_container_width=True)
    else:
        st.info("No player points props available at the moment.")

# --- Footer ---
st.markdown("---")
st.caption("Updated every 60 seconds — Line movement storage disabled on Streamlit Cloud for compatibility.")
