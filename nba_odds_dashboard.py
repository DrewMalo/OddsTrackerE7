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
# NOTE: The balldontlie SDK is not available in this environment.
# We'll use direct requests instead.
ODDS_API_KEY = '0c03cbe55c11b193e6d23407c48cc604'  # the-odds-api.com
BALLDONTLIE_API_KEY = '498117bc-f941-454d-a142-6aa8b6778cec'
BALLDONTLIE_BASE = 'https://www.balldontlie.io/api/v1'

# balldontlie.io SDK initialization
API_URL = 'https://api.the-odds-api.com/v4/sports/basketball_nba/odds'
API_EVENT_URL = 'https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/markets'

params = {
    'apiKey': ODDS_API_KEY,
    'regions': 'us',
    'markets': 'h2h,spreads,totals',
    'oddsFormat': 'american',
    'bookmakers': 'fanduel,draftkings,betmgm'
}

@st.cache_data(ttl=600)
def get_all_teams():
    try:
        response = requests.get(f"{BALLDONTLIE_BASE}/teams")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning(f"Failed to fetch teams from balldontlie.io: {e}")
        return {"data": []}
    except Exception as e:
        st.warning(f"Failed to fetch teams from balldontlie.io: {e}")
        return {"data": []}
    except Exception as e:
        st.warning(f"Failed to fetch teams from balldontlie.io: {e}")
        return {"data": []}

@st.cache_data(ttl=600)
def get_players(per_page=100):
    try:
        response = requests.get(f"{BALLDONTLIE_BASE}/players?per_page={per_page}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning(f"Failed to fetch players from balldontlie.io: {e}")
        return {"data": []}
    except Exception as e:
        st.warning(f"Failed to fetch players from balldontlie.io: {e}")
        return {"data": []}
    except Exception as e:
        st.warning(f"Failed to fetch players from balldontlie.io: {e}")
        return {"data": []}

@st.cache_data(ttl=60)
def fetch_odds():
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        st.caption(f"Requests remaining: {response.headers.get('x-requests-remaining')}, Used: {response.headers.get('x-requests-used')}")
        return response.json()
    except requests.exceptions.JSONDecodeError:
        st.error("Invalid JSON received from The Odds API.")
        return []
    except Exception as e:
        st.error(f"Failed to load odds: {e}")
        return []

@st.cache_data(ttl=60)
def fetch_player_props(event_id):
    url = API_EVENT_URL.format(event_id=event_id)
    response = requests.get(url, params={'apiKey': ODDS_API_KEY, 'markets': 'player_points', 'oddsFormat': 'american'})
    if response.status_code != 200:
        return []
    return response.json()

# --- Helper ---
def implied_prob(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return -odds / (-odds + 100)

# --- Independent Odds API Data ---
odds_data = fetch_odds()
games, props = [], []

# --- Independent balldontlie Data ---
all_teams = get_all_teams().get('data', [])
all_players = get_players(per_page=100).get('data', [])

# --- Data Processing ---
# ... (unchanged below this point)

