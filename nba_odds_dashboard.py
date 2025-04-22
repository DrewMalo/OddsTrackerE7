# nba_odds_tracker.py
import streamlit as st
import pandas as pd
import os  # Fix: Import os to use os.path.exists

# --- Placeholder data to ensure app runs before full data fetch ---
df = pd.DataFrame()
df_props = pd.DataFrame()
csv_file = 'nba_odds_history.csv'

# --- Tabs Layout ---
tabs = st.tabs([
    "\U0001F4CA Game Odds",
    "\U0001F4C8 Line Movement",
    "\U0001F3AF Player Props",
    "\U0001F9D1‍\U0001F3CB️ Player Stats",
    "\U0001F3C0 Shooting Averages"
])
tab1, tab2, tab3, tab4, tab5 = tabs

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
    if not df.empty:
        df_display = df.style.apply(highlight_best, axis=1)
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No game odds data available.")

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

with tab4:
    st.subheader("\U0001F9D1‍\U0001F3CB️ Player Stats from balldontlie.io")
    try:
        from nba_odds_tracker import get_stats
        stats = get_stats()
        stats_df = pd.DataFrame(stats['data'])
        if not stats_df.empty:
            st.dataframe(stats_df.head(100), use_container_width=True)
        else:
            st.info("No player stats available.")
    except Exception as e:
        st.error("Error loading player stats.")

with tab5:
    st.subheader("\U0001F3C0 Shooting Averages (2024 Regular Season)")
    try:
        from nba_odds_tracker import get_shooting_averages
        shooting = get_shooting_averages()
        shooting_df = pd.DataFrame(shooting['data'])
        if not shooting_df.empty:
            st.dataframe(shooting_df, use_container_width=True)
        else:
            st.info("No shooting averages data available.")
    except Exception as e:
        st.error("Error loading shooting averages.")

# --- Footer ---
st.markdown("---")
st.caption("Updated every 60 seconds — Line movement storage disabled on Streamlit Cloud for compatibility.")
