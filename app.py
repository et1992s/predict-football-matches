import base64
import json
import os
from datetime import datetime
from glob import glob
import pandas as pd
import streamlit as st
from live_score import LiveScoreService
from match_predictor import FootballMatchPredictor


class FootballXApp:
    def __init__(self):
        self.live_score_service = LiveScoreService()
        self.leagues = {
            "jupiler-pro-league-2025-2026": {"name": "Belgium Jupiler Pro League", "flag": "flags/belgium.png"},
            "premier-league-2025-2026": {"name": "England Premier League", "flag": "flags/england.png"},
            "france-ligue-1-2025-2026": {"name": "France Ligue 1", "flag": "flags/france.png"},
            "bundesliga-2025-2026": {"name": "Germany Bundesliga", "flag": "flags/germany.png"},
            "italy-serie-a-2025-2026": {"name": "Italy Series A", "flag": "flags/italy.png"},
            "liga-portugal-2025-2026": {"name": "Liga Portugal", "flag": "flags/portugal.png"},
            "netherlands-eredivisie-2025-2026": {"name": "Netherlands Eredivisie", "flag": "flags/netherlands.png"},
            "romania-superliga-2025-2026": {"name": "Romania Superliga", "flag": "flags/romania.png"},
            "la-liga-2025-2026": {"name": "Spain La Liga", "flag": "flags/spain.png"},
            "champions-league-2025-2026": {"name": "Champions League", "flag": "flags/europe.png"}}

        self.setup_page_config()
        self.setup_css()
        self.display_header()

    @staticmethod
    def setup_page_config():
        st.set_page_config(page_title="FootballX", layout="centered")

    @staticmethod
    def setup_css():
        css_file = "static/style.css"
        if os.path.exists(css_file):
            with open(css_file) as f:
                css = f.read()
                st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        else:
            st.warning(f"CSS file {css_file} not found.")

    @staticmethod
    def display_header():
        logo_path = "footballXlogo.png"
        with open(logo_path, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()

        st.markdown(f"""
            <div class="header-container">
                <img src="data:image/png;base64,{logo_base64}" class="header-logo">
                <h1 class="header-title">FootballX</h1>
            </div>
        """, unsafe_allow_html=True)

    def get_todays_matches(self, league_key):
        today = datetime.now().strftime("%d.%m.%Y")
        return self._get_matches_for_date(league_key, today)

    @st.cache_data(ttl=300)
    def _get_matches_for_date(_self, league_key, date):
        matches_file_json = f"processed/all-matches-{league_key}.json"
        fixtures_file_json = f"processed/fixtures-{league_key}.json"

        matches_today = []

        if os.path.exists(matches_file_json):
            with open(matches_file_json, "r", encoding="utf-8") as f:
                matches_data = json.load(f)
            df_matches = pd.json_normalize(matches_data["matches"])
            if not df_matches.empty:
                today_matches = df_matches[df_matches["date"] == date]
                matches_today.extend(today_matches.to_dict('records'))

        if os.path.exists(fixtures_file_json):
            with open(fixtures_file_json, "r", encoding="utf-8") as f:
                fixtures_data = json.load(f)
            df_fixtures = pd.json_normalize(fixtures_data["matches"])
            if not df_fixtures.empty:
                today_fixtures = df_fixtures[df_fixtures["date"] == date]
                matches_today.extend(today_fixtures.to_dict('records'))

        return matches_today

    def display_todays_matches(self):
        st.markdown(
            f'<div class="league-subheading" style="font-size: 24px; '
            f'text-align:center; padding: 5px; color: var(--text-primary); '
            f'margin-bottom: 22px; font-weight: bold;">{"Today\'s Matches"}</div>',
            unsafe_allow_html=True)

        league_matches = {}
        for league_key in self.leagues.keys():
            matches = self.get_todays_matches(league_key)
            if matches:
                league_matches[league_key] = matches

        if not league_matches:
            st.info("No matches scheduled for today")
            return

        for league_key, matches in league_matches.items():
            league_name = self.leagues[league_key]["name"]
            flag_path = self.leagues[league_key]["flag"]
            flag_base64 = self.get_flag_base64(flag_path)

            st.markdown(f"""
                <div class="todays-matches-container">
                    <div class="league-header">
                        {f'<img src="data:image/png;base64,{flag_base64}" class="flag-icon">' if flag_base64 else ''}
                        <h3 class="league-title">{league_name}</h3>
                        <span style="margin-left: auto; font-size: 14px; color: var(--text-primary); opacity: 0.7;">
                            {len(matches)} match{'' if len(matches) == 1 else 'es'}
                        </span>
                    </div>
            """, unsafe_allow_html=True)

            matches_sorted = sorted(matches, key=lambda x: x.get('time', '00:00'))

            for match in matches_sorted:
                home = match.get('home', 'TBD')
                away = match.get('away', 'TBD')
                time = match.get('time', 'TBD')
                status = match.get('status', '')
                home_score = match.get('home_score', '')
                away_score = match.get('away_score', '')

                status_class = "status-scheduled"
                if status.upper() in ['LIVE', '1H', '2H', 'HT', 'ET']:
                    status_class = "status-live"
                elif status.upper() in ['FT', 'AET', 'PEN']:
                    status_class = "status-finished"

                score_display = f"{home_score}-{away_score}" if home_score != '' and away_score != '' else "vs"

                st.markdown(f"""
                    <div class="match-card">
                        <div class="match-row">
                            <span class="match-time">{time}</span>
                            <span class="team-name team-home">{home}</span>
                            <span class="match-score">{score_display}</span>
                            <span class="team-name team-away">{away}</span>
                            <span class="match-status {status_class}">{status}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    @staticmethod
    def get_flag_base64(flag_path):
        try:
            if os.path.exists(flag_path):
                with open(flag_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            return ""
        except Exception as e:
            print(f"Error loading flag {flag_path}: {e}")
            return ""

    @staticmethod
    def get_all_winrate_files():
        """Get all winrate CSV files from processed directory"""
        winrate_files = glob("processed/standings-with-winrate-features-*.csv")
        return winrate_files

    def download_league_data(self, selected_league, league_info):
        """Download data for selected league"""
        # For combined predictions, we use all available datasets
        all_winrate_files = self.get_all_winrate_files()

        if not all_winrate_files:
            st.warning("No prediction data available. Please run data processing first.")
            return None, None, None, all_winrate_files

        return None, None, None, all_winrate_files

    @staticmethod
    def get_future_matches():
        """Get future matches from all available data"""
        return pd.DataFrame()

    def display_prediction_section(self, winrate_files):
        """Display prediction section with combined datasets"""
        with st.expander("Predict Future Match", expanded=True):
            if not winrate_files:
                st.warning("No prediction data available. Please process data first.")
                return

            all_teams = set()
            for file in winrate_files:
                df = pd.read_csv(file)
                if "Team" in df.columns:
                    all_teams.update(df["Team"].unique())
            all_teams = sorted(list(all_teams))

            col1, col2 = st.columns(2)
            with col1:
                home_team = st.selectbox("Home Team", all_teams, index=0)
            with col2:
                away_team = st.selectbox("Away Team", all_teams, index=1)

            if st.button("Predict Match"):
                if not home_team or not away_team:
                    st.warning("Please enter both home and away team names")
                    return
                with st.spinner("Predicting..."):
                    try:
                        predictor = FootballMatchPredictor(winrate_files)
                        predictor.train_models()
                        predictions = predictor.predict_future_match(home_team, away_team)
                        if not predictions or predictions.get('score') is None:
                            st.error("Could not generate prediction for this match. Not enough historical data.")
                            return
                        self._display_prediction_results(home_team, away_team, predictions)
                    except Exception as e:
                        st.error(f"Prediction failed: {str(e)}")

    @staticmethod
    def _display_prediction_results(home_team, away_team, predictions):
        """Display prediction results"""
        # Extract prediction data
        pred_outcome, proba_outcome = predictions['outcome']
        pred_goals = predictions['goals']
        pred_score = predictions['score']
        stats = predictions['stats']

        st.subheader("Prediction Details")

        # Outcome prediction
        outcome_mapping = {1: f"{home_team} Win", 2: f"{away_team} Win", 0: "Draw"}
        predicted_outcome = outcome_mapping.get(pred_outcome, "Unknown")

        # Columns for outcome probabilities
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"{home_team} Win", f"{proba_outcome[1] * 100:.1f}%")
        with col2:
            st.metric("Draw", f"{proba_outcome[0] * 100:.1f}%")
        with col3:
            st.metric(f"{away_team} Win", f"{proba_outcome[2] * 100:.1f}%")

        # Other predictions
        col4, col5, col6 = st.columns(3)
        with col4:
            st.metric("Predicted Outcome", predicted_outcome)
        with col5:
            st.metric("Total Goals", pred_goals)
        with col6:
            st.metric("Likely Score", pred_score)

        # Stats data
        home_stats = {
            'expected_goals': stats['home']['xg'],
            'ball_possession': stats['home']['possession'] * 100,  # Converting to percentage
            'total_shots': stats['home']['shots_total'],
            'shots_on_target': stats['home']['shots_on_target'],
            'fouls': stats['home']['fouls'],
            'corner_kicks': stats['home']['corners'],
            'yellow_cards': stats['home']['yellow_cards']
        }

        away_stats = {
            'expected_goals': stats['away']['xg'],
            'ball_possession': stats['away']['possession'] * 100,  # Converting to percentage
            'total_shots': stats['away']['shots_total'],
            'shots_on_target': stats['away']['shots_on_target'],
            'fouls': stats['away']['fouls'],
            'corner_kicks': stats['away']['corners'],
            'yellow_cards': stats['away']['yellow_cards']
        }

        display_names = {
            'expected_goals': 'xG',
            'ball_possession': 'Possession',
            'total_shots': 'Shots',
            'shots_on_target': 'On Target',
            'fouls': 'Fouls',
            'corner_kicks': 'Corners',
            'yellow_cards': 'Yellows'
        }

        st.subheader("Predicted Statistics")

        # This creates responsive stats comparison
        st.markdown("""<div class="stats-grid-container">""", unsafe_allow_html=True)

        # Stats comparison rows
        stats_keys = list(display_names.keys())

        for key in stats_keys:
            home_val = home_stats[key]
            away_val = away_stats[key]

            # Special handling for possession
            if key == 'ball_possession':
                home_percent = home_val
                away_percent = away_val
                home_display = f"{home_val:.0f}%"
                away_display = f"{away_val:.0f}%"
            else:
                # For other stats, this calculates percentages for comparison
                total = home_val + away_val
                if total > 0:
                    home_percent = (home_val / total) * 100
                    away_percent = (away_val / total) * 100
                else:
                    home_percent = away_percent = 50

                # Format display values
                if isinstance(home_val, float):
                    home_display = f"{home_val:.1f}"
                    away_display = f"{away_val:.1f}"
                else:
                    home_display = str(home_val)
                    away_display = str(away_val)

            st.markdown(f"""
                <div class="stats-row">
                    <div class="stat-item">
                        <div class="stat-label">{home_team}</div>
                        <div class="stat-value">{home_display}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">{display_names[key]}</div>
                        <div class="stat-value">VS</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">{away_team}</div>
                        <div class="stat-value">{away_display}</div>
                    </div>
            """, unsafe_allow_html=True)

            # This displays the comparison bars for statistics
            st.markdown(f"""
                        <div class="stat-comparison">
                            <div class="stat-bar reverse">
                                <div class="stat-bar-fill" style="width: {home_percent}%"></div>
                            </div>
                            <div class="stat-bar">
                                <div class="stat-bar-fill" style="width: {away_percent}%"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    def run(self):
        self.display_todays_matches()
        winrate_files = self.get_all_winrate_files()
        self.live_score_service.display_live_scores_from_api()
        self.display_prediction_section(winrate_files)


if __name__ == "__main__":
    app = FootballXApp()
    app.run()