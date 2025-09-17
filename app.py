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
        self.leagues = {
            "jupiler-pro-league-2025-2026": {
                "name": "Belgium Jupiler Pro League",
                "flag": "flags/belgium.png"
            },
            "premier-league-2025-2026": {
                "name": "England Premier League",
                "flag": "flags/england.png"
            },
            "france-ligue-1-2025-2026": {
                "name": "France Ligue 1",
                "flag": "flags/france.png",
            },
            "bundesliga-2025-2026": {
                "name": "Germany Bundesliga",
                "flag": "flags/germany.png",
            },
            "italy-serie-a-2025-2026": {
                "name": "Italy Series A",
                "flag": "flags/italy.png",
            },
            "liga-portugal-2025-2026": {
                "name": "Liga Portugal",
                "flag": "flags/portugal.png",
            },
            "netherlands-eredivisie-2025-2026": {
                "name": "Netherlands Eredivisie",
                "flag": "flags/netherlands.png",
            },
            "romania-superliga-2025-2026": {
                "name": "Romania Superliga",
                "flag": "flags/romania.png",
            },
            "la-liga-2025-2026": {
                "name": "Spain La Liga",
                "flag": "flags/spain.png",
            },
            "champions-league-2025-2026": {
                "name": "Champions League",
                "flag": "flags/europe.png",
            },
        }

        self.setup_page_config()
        self.setup_css()
        self.display_header()

    def setup_page_config(self):
        st.set_page_config(page_title="FootballX", layout="wide")

    def setup_css(self):
        st.markdown("""
            <style>
            /* ===== THEME VARIABLES ===== */
            :root {
                --bg-primary: var(--background-color);
                --text-primary: var(--text-color);
                --card-bg: color-mix(in srgb, var(--bg-primary) 85%, transparent);
                --border-color: color-mix(in srgb, var(--text-primary) 20%, transparent);
                --accent-color: #A8D5BA;
                --highlight-color: #E6DFB2;
                --success-color: #27ae60;
                --warning-color: #f39c12;
                --danger-color: #e74c3c;
            }
            
            /* ===== STATS CARDS ===== */
            .stats-card {
                background: var(--card-bg) !important;
                border: 1px solid var(--border-color) !important;
                padding: 5px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                text-align: left;
                min-width: 0;
            }
            .stats-label {
                font-size: 14px;
                color: var(--text-primary);
                opacity: 0.9;
                margin-bottom: 8px;
                font-weight: 500;
            }
            .stats-value {
                font-size: 24px;
                font-weight: bold;
                color: var(--highlight-color);
                margin: 8px 0;
            }
            
            /* ===== PROGRESS BARS ===== */
            .progress-container {
                height: 8px;
                background: color-mix(in srgb, var(--border-color) 50%, transparent);
                border-radius: 4px;
                margin: 10px 0;
                overflow: hidden;
            }
            .progress-container.reverse {
                display: flex;
                justify-content: flex-end;
            }
            .progress-fill {
                height: 100%;
                background: var(--accent-color);
                border-radius: 4px;
            }
            
            /* ===== PREDICTED MATCH STATS GRID ===== */
            .stats-grid {
                display: flex !important;
                gap: 20px;
                justify-content: space-between;
                flex-wrap: nowrap; /* menține două coloane principale */
            }
            .stats-grid > div {
                flex: 1 1 48%;
                min-width: 150px;
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
            }
            .stats-grid > div:nth-child(2) .stats-card {
                text-align: right; /* cardurile echipei away */
            }
            .stats-card {
                flex: 1 1 48%; /* două carduri pe rând */
                min-width: 120px;
                margin-bottom: 12px;
                padding: 5px;
                background: var(--card-bg) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                border-radius: 8px;
                text-align: left;
            }
            
            /* ===== TODAY'S MATCHES STYLING ===== */
            .todays-matches-container {
                background: var(--card-bg) !important;
                border: 0px solid var(--border-color) !important;
                border-radius: 50px !important;
                padding: 20px;
                margin: 0px;
                margin-top: -20px;
                box-shadow: 0 4px 4px rgba(0,0,0,1.9);
            }
            .league-header {
                display: flex;
                align-items: center;
                gap: 5px;
                margin-top: -20px;
                margin-bottom: 5px;
                padding-bottom: 0px;
                border-bottom: 0px solid var(--border-color);
            }
            .league-title {
                font-size: 18px;
                font-weight: bold;
                color: var(--accent-color);
                margin: 0;
            }
            .match-card {
                background: color-mix(in srgb, var(--card-bg) 95%, transparent) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 100px !important;
                padding: 14px;
                margin-bottom: 12px;
                transition: all 0.3s ease;
            }
            .match-card:hover {
                border-color: var(--accent-color) !important;
                box-shadow: 0 4px 8px rgba(168, 213, 186, 0.2);
                transform: translateY(-2px);
            }
            .match-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0px;
                width: 100%;
            }
            .match-time {
                min-width: 60px;
                color: var(--highlight-color);
                text-align: center;
                background: color-mix(in srgb, var(--border-color) 0%, transparent);
                padding: 6px 8px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            .team-name {
                flex: 1;
                font-weight: 500;
                color: var(--text-primary);
                text-align: center;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .team-home { text-align: right; }
            .team-away { text-align: left; }
            .match-score {
                min-width: 30px;
                font-weight: bold;
                color: var(--highlight-color);
                text-align: center;
                font-size: 16px;
                margin: 0 8px;
            }
            .status-live {
                background: linear-gradient(45deg, #ff6b6b, #ee5a24) !important;
                color: white !important;
            }
            .status-finished {
                background: color-mix(in srgb, var(--success-color) 20%, transparent) !important;
                color: var(--success-color) !important;
            }
            .status-scheduled {
                background: color-mix(in srgb, var(--border-color) 20%, transparent) !important;
                color: var(--text-primary) !important;
            }
            .flag-icon {
                width: 25px;
                height: 16px;
                object-fit: cover;
                border-radius: 2px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            /* ===== LIVE MATCH STYLING ===== */
            .live-match-container {
                background: var(--card-bg) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 12px !important;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            .live-match-card {
                background: color-mix(in srgb, var(--card-bg) 95%, transparent) !important;
                border-left: 4px solid;
                border-radius: 8px !important;
                padding: 14px;
                margin-bottom: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .live-match-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                width: 100%;
            }
            .live-team-name {
                flex: 2;
                font-weight: 500;
                font-size: 13px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .live-team-home { text-align: left; }
            .live-team-away { text-align: right; }
            .live-match-score {
                flex: 1;
                font-weight: bold;
                font-size: 16px;
                text-align: center;
                padding: 0 5px;
            }
            .live-match-status {
                min-width: 80px;
                text-align: center;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 8px;
                border-radius: 6px;
                color: white;
                margin-top: 4px;
            }
            
            /* ===== STREAMLIT OVERRIDES ===== */
            .stApp, [data-testid="stAppViewContainer"] {
                background: var(--bg-primary) !important;
                color: var(--text-primary) !important;
            }
            div[data-testid="stMetric"] {
                background: var(--card-bg) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 12px !important;
                padding: 12px !important;
                color: var(--text-primary) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            div[data-testid="stMetricValue"] {
                color: var(--highlight-color) !important;
                font-weight: bold !important;
                font-size: 22px !important;
            }
            .stMarkdown h3 {
                color: var(--accent-color) !important;
                font-weight: 100 !important;
                font-size: 16px !important;
                font-family: sans-serif;
            }
            .stMarkdown h1 {
                color: var(--highlight-color) !important;
                font-size: 36px !important;
                font-family: Lucida Console, Monospace;
            }
            .stDataFrame th {
                background-color: var(--card-bg) !important;
                color: var(--text-primary) !important;
                font-weight: bold !important;
            }
            .stDataFrame td {
                background-color: var(--card-bg) !important;
                color: var(--text-primary) !important;
            }
            
            /* ===== SELECTBOX STYLING ===== */
            div.stSelectbox label {
                color: var(--text-primary) !important;
                font-weight: bold !important;
                margin-bottom: 6px !important;
            }
            div[data-baseweb="select"] > div {
                background: var(--card-bg) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 10px !important;
                padding: 12px 16px !important;
                min-height: 50px !important;
                display: flex;
                align-items: center;
                color: var(--text-primary) !important;
                font-size: 16px !important;
                transition: all 0.3s ease !important;
            }
            div[data-baseweb="select"] > div:hover {
                border: 1px solid var(--accent-color) !important;
                background: color-mix(in srgb, var(--card-bg) 90%, black) !important;
            }
            div[data-baseweb="select"] > div:focus-within {
                border: 2px solid var(--highlight-color) !important;
                box-shadow: 0 0 8px color-mix(in srgb, var(--highlight-color) 40%, transparent) !important;
            }
            div[data-baseweb="select"] ul {
                background: var(--card-bg) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 8px !important;
            }
            div[data-baseweb="select"] li {
                background: transparent !important;
                color: var(--text-primary) !important;
            }
            div[data-baseweb="select"] li:hover {
                background: color-mix(in srgb, var(--card-bg) 80%, black) !important;
                color: var(--text-primary) !important;
            }
            
            /* ===== BUTTONS ===== */
            div.stButton > button {
                background: var(--card-bg) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 10px !important;
                margin-left: 75px;
                font-size: 16px !important;
                font-weight: bold !important;
                transition: all 0.3s ease-in-out !important;
            }
            div.stButton > button:hover {
                background: color-mix(in srgb, var(--card-bg) 80%, black) !important;
                border: 1px solid var(--accent-color) !important;
            }
            
            /* ===== SPINNER ===== */
            .stSpinner > div {
                color: var(--text-primary) !important;
                font-size: 18px !important;
                font-weight: bold !important;
            }
            
            /* ===== DARK/LIGHT THEMES ===== */
            @media (prefers-color-scheme: dark) {
                :root {
                    --background-color: #0E1A2B;
                    --text-color: #E0F7FA;
                }
            }
            @media (prefers-color-scheme: light) {
                :root {
                    --background-color: #F0F8FF;
                    --text-color: #1E3C72;
                }
            }
            
            /* ===== RESPONSIVE DESIGN ===== */
            @media (max-width: 768px) {
                .stats-grid { flex-wrap: wrap; gap: 10px; justify-content: space-between; }
                .team-home, .team-away, .live-team-home, .live-team-away { text-align: center; }
                .stats-card { flex: 1 1 45%; min-width: 140px; font-size: 13px; }
                .stats-label { font-size: 13px !important; }
                .stats-value { font-size: 20px !important; }
            }
            @media (max-width: 480px) {
                .todays-matches-container, .live-match-container { padding: 0px; }
                .match-card, .live-match-card { padding: 10px; }
                .team-name, .live-team-name { font-size: 11px; }
                .match-score, .live-match-score { font-size: 14px; }
                .stats-card { flex: 1 1 45%; min-width: 140px; }
                .stats-label { font-size: 12px !important; }
                .stats-value { font-size: 18px !important; }
            }
            @media (min-width: 300px) {
                .stats-grid { flex-wrap: wrap; gap: 10px; justify-content: space-between; }
                .stats-card { flex: 1 1 45%; min-width: 140px; }
                .stats-label { font-size: 11px !important; }
                .stats-value { font-size: 16px !important; }
                .match-card, .live-match-card { padding: 8px !important; }
                .team-name, .live-team-name { font-size: 11px !important; }
            }
            </style>

        """, unsafe_allow_html=True)

    def display_header(self):
        logo_path = "footballXlogo.png"
        with open(logo_path, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()

        st.markdown(f"""
            <style>
            .header-container {{
                display: flex;
                align-items: center;
                justify-content: flex-start;
                gap: 15px;
                padding: 10px 0;
                margin-bottom: 20px;
            }}
            .header-logo {{
                width: 80px;
                height: auto;
            }}
            .header-title {{
                font-size: 42px;
                font-weight: bold;
                color: var(--highlight-color);
                margin: 0;
            }}
            </style>
            <div class="header-container">
                <img src="data:image/png;base64,{logo_base64}" class="header-logo">
                <h1 class="header-title">FootballX</h1>
            </div>
        """, unsafe_allow_html=True)

    def display_live_scores_from_api(self):
        """Display live scores from API-Football"""
        st.markdown(f'<div class="league-subheading">{"⚽ Live Scores Today"}</div>', unsafe_allow_html=True)
        try:
            # Inițializează serviciul
            live_service = LiveScoreService()
            live_matches = live_service.get_today_live_matches()

            if not live_matches:
                st.info("📺 No live matches at the moment")
                return

            # Grupează meciurile pe ligi
            matches_by_league = {}
            for match in live_matches:
                league_name = f"{match['country']} - {match['league']}"
                if league_name not in matches_by_league:
                    matches_by_league[league_name] = []
                matches_by_league[league_name].append(match)

            # Afișează meciurile grupate pe ligi
            for league_name, matches in matches_by_league.items():
                with st.expander(f"🏆 {league_name} ({len(matches)} matches)", expanded=False):
                    for match in matches:
                        self._display_api_match(match)

        except Exception as e:
            st.error(f"❌ Error loading live scores: {e}")

    def _display_api_match(self, match):
        """Display a single match from API with mapped statuses"""
        status = match['status']
        home_goals = match['home_goals']
        away_goals = match['away_goals']
        fixture_time = match.get('time')
        elapsed = match.get('elapsed')

        # Gestionează scorurile None
        if home_goals is None or away_goals is None:
            score_display = "-"
            score_style = "font-weight: bold; font-size: 16px; color: #95a5a6;"
        else:
            score_display = f"{home_goals} - {away_goals}"
            score_style = "font-weight: bold; font-size: 18px; color: #FFFFFF;"

        # Mapare statusuri API → text și stil
        def map_status(status, elapsed, fixture_time):
            if status in ("TBD", "NS"):
                return f"{fixture_time}", "#3498db", "rgba(52, 152, 219, 0.1)"
            elif status == "1H":
                return f"LIVE {elapsed}'", "white", "linear-gradient(45deg, #ff6b6b, #ee5a24)"
            elif status == "HT":
                return "⏸HALF TIME", "white", "linear-gradient(45deg, #f39c12, #d35400)"
            elif status == "2H":
                return f"LIVE {elapsed}'", "white", "linear-gradient(45deg, #ff6b6b, #ee5a24)"
            elif status == "ET":
                return f"ET {elapsed}'", "white", "linear-gradient(45deg, #8e44ad, #9b59b6)"
            elif status == "BT":
                return "⏸BREAK", "#f39c12", "rgba(243, 156, 18, 0.2)"
            elif status == "P":
                return f"PEN {elapsed}'", "white", "linear-gradient(45deg, #2c3e50, #34495e)"
            elif status == "FT":
                return "FINAL", "#27ae60", "rgba(46, 204, 113, 0.15)"
            elif status == "AET":
                return "AET FINAL", "#27ae60", "rgba(46, 204, 113, 0.15)"
            elif status == "PEN":
                return "PEN FINAL", "#27ae60", "rgba(46, 204, 113, 0.15)"
            elif status == "SUSP":
                return "⏸SUSPENDED", "#7f8c8d", "rgba(149, 165, 166, 0.2)"
            elif status == "INT":
                return "⏸INTERRUPTED", "#7f8c8d", "rgba(149, 165, 166, 0.2)"
            elif status == "PST":
                return "POSTPONED", "#7f8c8d", "rgba(149, 165, 166, 0.2)"
            elif status == "CANC":
                return "CANCELED", "#7f8c8d", "rgba(149, 165, 166, 0.2)"
            elif status == "ABD":
                return "ABANDONED", "#7f8c8d", "rgba(149, 165, 166, 0.2)"
            elif status == "AWD":
                return "AWARDED", "#c0392b", "rgba(231, 76, 60, 0.2)"
            elif status == "WO":
                return "WALKOVER", "#c0392b", "rgba(231, 76, 60, 0.2)"
            elif status == "LIVE":
                return f"LIVE {elapsed}'", "white", "linear-gradient(45deg, #ff6b6b, #ee5a24)"
            else:
                return f"{fixture_time}", "#3498db", "rgba(52, 152, 219, 0.1)"

        status_text, text_color, bg_color = map_status(status, elapsed, fixture_time)
        team_style = "font-weight: bold; font-size: 13px;"

        # Render în Streamlit
        st.markdown(f"""
            <div style="
                background: {bg_color};
                color: {text_color};
                padding: 10px;
                border-radius: 8px;
                margin: 6px 0;
                border-left: 4px solid {text_color};
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 2; {team_style}; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        {match['home']}
                    </div>
                    <div style="flex: 1; {score_style}; text-align: center; padding: 0 5px;">
                        {score_display}
                    </div>
                    <div style="flex: 2; {team_style}; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        {match['away']}
                    </div>
                </div>
                <div style="text-align: center; font-size: 11px; color: white; margin-top: 4px;">
                    {status_text} • {match.get('round', '')}
                </div>
            </div>
        """, unsafe_allow_html=True)

    def get_todays_matches(self, league_key):
        """Get today's matches for a league with caching"""
        today = datetime.now().strftime("%d.%m.%Y")
        return self._get_matches_for_date(league_key, today)

    @st.cache_data(ttl=300)  # Cache pentru 5 minute
    def _get_matches_for_date(_self, league_key, date):
        """Internal method with caching"""
        matches_file_json = f"processed/all-matches-{league_key}.json"
        fixtures_file_json = f"processed/fixtures-{league_key}.json"

        matches_today = []

        # Check results
        if os.path.exists(matches_file_json):
            with open(matches_file_json, "r", encoding="utf-8") as f:
                matches_data = json.load(f)
            df_matches = pd.json_normalize(matches_data["matches"])
            if not df_matches.empty:
                today_matches = df_matches[df_matches["date"] == date]
                matches_today.extend(today_matches.to_dict('records'))

        # Check fixtures
        if os.path.exists(fixtures_file_json):
            with open(fixtures_file_json, "r", encoding="utf-8") as f:
                fixtures_data = json.load(f)
            df_fixtures = pd.json_normalize(fixtures_data["matches"])
            if not df_fixtures.empty:
                today_fixtures = df_fixtures[df_fixtures["date"] == date]
                matches_today.extend(today_fixtures.to_dict('records'))

        return matches_today

    def display_todays_matches(self):
        """Display today's matches with dropdowns by league"""
        st.markdown(
            f'<div class="league-subheading" style="font-size: 24px; color: var(--accent-color); '
            f'margin-bottom: 20px; font-weight: bold;">{"📅 Today\'s Matches"}</div>',
            unsafe_allow_html=True)

        # Group matches by league
        league_matches = {}
        for league_key in self.leagues.keys():
            matches = self.get_todays_matches(league_key)
            if matches:
                league_matches[league_key] = matches

        if not league_matches:
            st.info("📋 No matches scheduled for today")
            return

        # Display matches in styled containers by league
        for league_key, matches in league_matches.items():
            league_name = self.leagues[league_key]["name"]
            flag_path = self.leagues[league_key]["flag"]
            flag_base64 = self.get_flag_base64(flag_path)

            # Create styled container for each league
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

            # Sort matches
            matches_sorted = sorted(matches, key=lambda x: x.get('time', '00:00'))

            for match in matches_sorted:
                home = match.get('home', 'TBD')
                away = match.get('away', 'TBD')
                time = match.get('time', 'TBD')
                status = match.get('status', '')
                home_score = match.get('home_score', '')
                away_score = match.get('away_score', '')

                # Determine status class
                status_class = "status-scheduled"
                if status.upper() in ['LIVE', '1H', '2H', 'HT', 'ET']:
                    status_class = "status-live"
                elif status.upper() in ['FT', 'AET', 'PEN']:
                    status_class = "status-finished"

                # Display score if available
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

    def get_flag_base64(self, flag_path):
        """Convert flag image to base64"""
        try:
            if os.path.exists(flag_path):
                with open(flag_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            return ""
        except Exception as e:
            print(f"Error loading flag {flag_path}: {e}")
            return ""

    def get_all_winrate_files(self):
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

    def get_future_matches(self):
        """Get future matches from all available data"""
        return pd.DataFrame()

    def display_prediction_section(self, winrate_files):
        """Display prediction section with combined datasets"""
        with st.expander("⚽ Predict Future Match", expanded=True):
            if not winrate_files:
                st.warning("No prediction data available. Please process data first.")
                return

            # Manual team input
            col1, col2 = st.columns(2)
            with col1:
                home_team = st.text_input("Home Team", placeholder="Enter home team name")
            with col2:
                away_team = st.text_input("Away Team", placeholder="Enter away team name")

            if st.button("Predict Match"):
                if not home_team or not away_team:
                    st.warning("Please enter both home and away team names")
                    return

                with st.spinner("Generating predictions... This may take a few moments!"):
                    try:
                        predictor = FootballMatchPredictor(winrate_files)
                        predictor.train_models()

                        predictions = predictor.predict_future_match(home_team, away_team)

                        if not predictions or predictions.get('score') is None:
                            st.error(
                                "Could not generate prediction for this match. The teams may not have sufficient historical data.")
                            return

                        self._display_prediction_results(home_team, away_team, predictions)

                    except Exception as e:
                        st.error(f"Prediction failed: {str(e)}")

    def _display_prediction_results(self, home_team, away_team, predictions):
        """Display prediction results"""
        # Extract prediction data
        pred_outcome, proba_outcome = predictions['outcome']
        pred_goals = predictions['goals']
        pred_score = predictions['score']
        stats = predictions['stats']

        st.subheader("📊 Prediction Details")
        # Outcome prediction
        outcome_mapping = {1: f"{home_team} Win", 2: f"{away_team} Win", 0: "Draw"}
        predicted_outcome = outcome_mapping.get(pred_outcome, "Unknown")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"{home_team} Win Probability", f"{proba_outcome[1] * 100:.1f}%")
        with col2:
            st.metric("Draw Probability", f"{proba_outcome[0] * 100:.1f}%")
        with col3:
            st.metric(f"{away_team} Win Probability", f"{proba_outcome[2] * 100:.1f}%")

        st.metric("Predicted Outcome", predicted_outcome)
        st.metric("Predicted Total Goals", pred_goals)
        st.metric("Most Likely Score", pred_score)

        # Valorile Home / Away din stats
        home_stats = {
            'expected_goals': stats['home']['xg'],
            'ball_possession': stats['home']['possession'] * 100,  # procent
            'total_shots': stats['home']['shots_total'],
            'shots_on_target': stats['home']['shots_on_target'],
            'fouls': stats['home']['fouls'],
            'corner_kicks': stats['home']['corners'],
            'yellow_cards': stats['home']['yellow_cards']
        }

        away_stats = {
            'expected_goals': stats['away']['xg'],
            'ball_possession': stats['away']['possession'] * 100,
            'total_shots': stats['away']['shots_total'],
            'shots_on_target': stats['away']['shots_on_target'],
            'fouls': stats['away']['fouls'],
            'corner_kicks': stats['away']['corners'],
            'yellow_cards': stats['away']['yellow_cards']
        }

        display_names = {
            'expected_goals': 'Expected Goals (xG)',
            'ball_possession': 'Ball Possession',
            'total_shots': 'Total Shots',
            'shots_on_target': 'Shots on Target',
            'fouls': 'Total Fouls',
            'corner_kicks': 'Corner Kicks',
            'yellow_cards': 'Yellow Cards'
        }

        st.subheader("📈 Predicted Match Statistics")
        col1, col2 = st.columns(2)

        # Home column
        with col1:
            st.markdown(f"""<div class="stats-card">
                                <div>
                                    <h4 style='text-align:left'>{home_team}</h4>""", unsafe_allow_html=True)
            for key in display_names:
                value = home_stats[key]
                if key == 'ball_possession':
                    st.markdown(f"""
                        <div class="stats-card">
                            <div class="stat-label">{display_names[key]}</div>
                            <div class="stat-value">{value:.0f}%</div>
                            <div class="progress-container reverse">
                                <div class="progress-fill" style="width: {value:.0f}%"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                elif key == 'expected_goals':
                    st.markdown(f"""
                            <div class="stats-card">
                                <div class="stats-label">{display_names[key]}</div>
                                <div class="stats-value">{value:.2f}</div>
                                <div class="progress-container reverse">
                                    <div class="progress-fill" style="width: {value:.0f}%"></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="stats-card">
                            <div class="stats-label">{display_names[key]}</div>
                            <div class="stats-value">{value}</div>
                            <div class="progress-container reverse">
                                <div class="progress-fill" style="width: {value:.0f}%"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        # Away column
        with col2:
            st.markdown(f"""<div class="stats-card">
                                <div>
                                    <h4 style='text-align:right'>{away_team}</h4>""", unsafe_allow_html=True)
            for key in display_names:
                value = away_stats[key]
                if key == 'ball_possession':
                    st.markdown(f"""
                        <div class="stats-card" style='text-align: right;'>
                            <div class="stats-label" style='text-align: right;'>{display_names[key]}</div>
                            <div class="stats-value" style='text-align: right;'>{value:.0f}%</div>
                            <div class="progress-container">
                                <div class="progress-fill" style="width: {value:.0f}%"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                elif key == 'expected_goals':
                    st.markdown(f"""
                            <div class="stats-card" style='text-align: right;'>
                                <div class="stats-label" style='text-align: right;'>{display_names[key]}</div>
                                <div class="stats-value" style='text-align: right;'>{value:.2f}</div>
                                <div class="progress-container">
                                    <div class="progress-fill" style="width: {value:.0f}%"></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="stats-card" style='text-align: right;'>
                            <div class="stats-label" style='text-align: right;'>{display_names[key]}</div>
                            <div class="stats-value" style='text-align: right;'>{value}</div>
                            <div class="progress-container">
                                <div class="progress-fill" style="width: {value:.0f}%"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    def run(self):
        """Main method to run the app"""
        # Display today's matches
        self.display_todays_matches()
        # Display live scores from API
        self.display_live_scores_from_api()
        winrate_files = self.get_all_winrate_files()
        # Display prediction section with combined datasets
        self.display_prediction_section(winrate_files)


# Run the app
if __name__ == "__main__":
    app = FootballXApp()
    app.run()