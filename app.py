import base64
import streamlit as st
import requests
import pandas as pd
import os
import base64
import json
from datetime import datetime
import altair as alt
from match_predictor import FootballMatchPredictor
from live_score import LiveScoreService
from main import scrape_and_save_standings, scrape_and_save_matches, scrape_and_save_fixtures, StandingsProcessor, \
    MatchPreprocessor, FootballWinRateFeatures


class FootballXApp:
    def __init__(self):
        self.leagues = {
            "jupiler-pro-league-2024-2025": {
                "name": "Belgium Jupiler Pro League 2024/2025",
                "flag": "flags/belgium.png",
                "standings_url": "https://www.flashscore.com/football/belgium/jupiler-pro-league-2024-2025/standings/#/v7MrIGpM/standings/overall/",
                "results_url": "https://www.flashscore.com/football/belgium/jupiler-pro-league-2024-2025/results/"
            },
            "jupiler-pro-league-2025-2026": {
                "name": "Belgium Jupiler Pro League 2025/2026",
                "flag": "flags/belgium.png",
                "standings_url": "https://www.flashscore.com/football/belgium/jupiler-pro-league/standings/#/WbIIL8v0/live-standings/",
                "results_url": "https://www.flashscore.com/football/belgium/jupiler-pro-league/results/",
                "fixtures_url": "https://www.flashscore.com/football/belgium/jupiler-pro-league/fixtures/"
            },
            "premier-league-2024-2025": {
                "name": "England Premier League 2024/2025",
                "flag": "flags/england.png",
                "standings_url": "https://www.flashscore.com/football/england/premier-league-2024-2025/standings/#/lAkHuyP3/standings/overall/",
                "results_url": "https://www.flashscore.com/football/england/premier-league-2024-2025/results/"
            },
            "premier-league-2025-2026": {
                "name": "England Premier League 2025/2026",
                "flag": "flags/england.png",
                "standings_url": "https://www.flashscore.com/football/england/premier-league/standings/#/OEEq9Yvp/standings/overall/",
                "results_url": "https://www.flashscore.com/football/england/premier-league/results/",
                "fixtures_url": "https://www.flashscore.com/football/england/premier-league/fixtures/"
            },
            "france-ligue-1-2024-2025": {
                "name": "France Ligue 1 2024/2025",
                "flag": "flags/france.png",
                "standings_url": "https://www.flashscore.com/football/france/ligue-1-2024-2025/standings/#/WYO1P5ch/standings/overall/",
                "results_url": "https://www.flashscore.com/football/france/ligue-1-2024-2025/results/"
            },
            "france-ligue-1-2025-2026": {
                "name": "France Ligue 1 2025/2026",
                "flag": "flags/france.png",
                "standings_url": "https://www.flashscore.com/football/france/ligue-1/standings/#/j9QeTLPP/live-standings/",
                "results_url": "https://www.flashscore.com/football/france/ligue-1/results/",
                "fixtures_url": "https://www.flashscore.com/football/france/ligue-1/fixtures/"
            },
            "bundesliga-2024-2025": {
                "name": "Germany Bundesliga 2024/2025",
                "flag": "flags/germany.png",
                "standings_url": "https://www.flashscore.com/football/germany/bundesliga-2024-2025/standings/#/8l1ZdrsC/standings/overall/",
                "results_url": "https://www.flashscore.com/football/germany/bundesliga-2024-2025/results/"
            },
            "bundesliga-2025-2026": {
                "name": "Germany Bundesliga 2025/2026",
                "flag": "flags/germany.png",
                "standings_url": "https://www.flashscore.com/football/germany/bundesliga/standings/#/8l1ZdrsC/standings/overall/",
                "results_url": "https://www.flashscore.com/football/germany/bundesliga/results/",
                "fixtures_url": "https://www.flashscore.com/football/germany/bundesliga/fixtures/"
            },
            "italy-serie-a-2024-2025": {
                "name": "Italy Series A 2024/2025",
                "flag": "flags/italy.png",
                "standings_url": "https://www.flashscore.com/football/italy/serie-a-2024-2025/standings/#/zDpS37lb/standings/overall/",
                "results_url": "https://www.flashscore.com/football/italy/serie-a-2024-2025/results/"
            },
            "italy-serie-a-2025-2026": {
                "name": "Italy Series A 2025/2026",
                "flag": "flags/italy.png",
                "standings_url": "https://www.flashscore.com/football/italy/serie-a/standings/#/6PWwAsA7/live-standings/",
                "results_url": "https://www.flashscore.com/football/italy/serie-a/results/",
                "fixtures_url": "https://www.flashscore.com/football/italy/serie-a/fixtures/"
            },
            "liga-portugal-2024-2025": {
                "name": "Liga Portugal 2024/2025",
                "flag": "flags/portugal.png",
                "standings_url": "https://www.flashscore.com/football/portugal/liga-portugal-2024-2025/standings/#/0d7EBBWo/standings/overall/",
                "results_url": "https://www.flashscore.com/football/portugal/liga-portugal-2024-2025/results/"
            },
            "liga-portugal-2025-2026": {
                "name": "Liga Portugal 2025/2026",
                "flag": "flags/portugal.png",
                "standings_url": "https://www.flashscore.com/football/portugal/liga-portugal-2024-2025/standings/#/0d7EBBWo/standings/overall/",
                "results_url": "https://www.flashscore.com/football/portugal/liga-portugal/results/",
                "fixtures_url": "https://www.flashscore.com/football/portugal/liga-portugal/fixtures/"
            },
            "netherlands-eredivisie-2024-2025": {
                "name": "Netherlands Eredivisie 2024/2025",
                "flag": "flags/netherlands.png",
                "standings_url": "https://www.flashscore.com/football/netherlands/eredivisie-2024-2025/standings/#/KCMrEcSo/standings/overall/",
                "results_url": "https://www.flashscore.com/football/netherlands/eredivisie-2024-2025/results/"
            },
            "netherlands-eredivisie-2025-2026": {
                "name": "Netherlands Eredivisie 2025/2026",
                "flag": "flags/netherlands.png",
                "standings_url": "https://www.flashscore.com/football/netherlands/eredivisie/standings/#/dWKtjvdd/standings/overall/",
                "results_url": "https://www.flashscore.com/football/netherlands/eredivisie/results/",
                "fixtures_url": "https://www.flashscore.com/football/netherlands/eredivisie/fixtures/"
            },
            "romania-superliga-2024-2025": {
                "name": "Romania Superliga 2024/2025",
                "flag": "flags/romania.png",
                "standings_url": "https://www.flashscore.com/football/romania/superliga-2024-2025/standings/#/QkBSrPPD/standings/overall/",
                "results_url": "https://www.flashscore.com/football/romania/superliga-2024-2025/results/"
            },
            "romania-superliga-2025-2026": {
                "name": "Romania Superliga 2025/2026",
                "flag": "flags/romania.png",
                "standings_url": "https://www.flashscore.com/football/romania/superliga/standings/#/02YI7tIj/standings/overall/",
                "results_url": "https://www.flashscore.com/football/romania/superliga/results/",
                "fixtures_url": "https://www.flashscore.com/football/romania/superliga/fixtures/"
            },
            "la-liga-2024-2025": {
                "name": "Spain La Liga 2024/2025",
                "flag": "flags/spain.png",
                "standings_url": "https://www.flashscore.com/football/spain/laliga-2024-2025/standings/#/dINOZk9Q/standings/overall/",
                "results_url": "https://www.flashscore.com/football/spain/laliga-2024-2025/results/",
            },
            "la-liga-2025-2026": {
                "name": "Spain La Liga 2025/2026",
                "flag": "flags/spain.png",
                "standings_url": "https://www.flashscore.com/football/spain/laliga/standings/#/vcm2MhGk/",
                "results_url": "https://www.flashscore.com/football/spain/laliga/results/",
                "fixtures_url": "https://www.flashscore.com/football/spain/laliga/fixtures/"
            },
            "champions-league-2024-2025": {
                "name": "Champions League 2024/2025",
                "flag": "flags/europe.png",
                "standings_url": "https://www.flashscore.com/football/europe/champions-league-2024-2025/standings/#/2oN82Fw5/",
                "results_url": "https://www.flashscore.com/football/europe/champions-league-2024-2025/results/"
            },
            "champions-league-2025-2026": {
                "name": "Champions League 2025/2026",
                "flag": "flags/europe.png",
                "standings_url": None,
                "results_url": None,
                "fixtures_url": "https://www.flashscore.com/football/europe/champions-league/fixtures/"
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
            /* ===== SYSTEM THEME AWARE STYLING ===== */
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

            /* ===== FUNDAL APP ===== */
            .stApp, [data-testid="stAppViewContainer"] {
                background: var(--bg-primary) !important;
                color: var(--text-primary) !important;
            }

            /* ===== CARDURI / CONTAINERE ===== */
            .css-1d391kg, div[data-testid="stMetric"] {
                background: var(--card-bg) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 12px !important;
                padding: 12px !important;
                color: var(--text-primary) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }

            /* ===== HEADINGS ===== */
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
                color: var(--accent-color) !important;
                font-weight: bold !important;
            }
            .league-title, .league-subheading {
                font-size: 24px !important;
                color: var(--accent-color) !important;
            }

            /* ===== TABEL ===== */
            .stDataFrame th {
                background-color: var(--card-bg) !important;
                color: var(--text-primary) !important;
                font-weight: bold !important;
            }
            .stDataFrame td {
                background-color: var(--card-bg) !important;
                color: var(--text-primary) !important;
            }

            /* ===== DROPDOWN / SELECTBOX ===== */
            div.stSelectbox {
                background: transparent !important;
            }
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
            div[data-baseweb="select"] span, 
            div[data-baseweb="select"] svg {
                color: var(--text-primary) !important;
                fill: var(--text-primary) !important;
            }

            /* ===== BUTTON ===== */
            div.stButton > button {
                background: var(--card-bg) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 10px !important;
                padding: 10px 20px !important;
                font-size: 16px !important;
                font-weight: bold !important;
                transition: all 0.3s ease-in-out !important;
            }
            div.stButton > button:hover {
                background: color-mix(in srgb, var(--card-bg) 80%, black) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--accent-color) !important;
            }

            /* ===== METRICS ===== */
            div[data-testid="stMetricValue"] {
                color: var(--highlight-color) !important;
                font-weight: bold !important;
                font-size: 22px !important;
            }

            /* ===== SPINNER ===== */
            .stSpinner > div {
                color: var(--text-primary) !important;
                font-size: 18px !important;
                font-weight: bold !important;
            }

            /* ===== CUSTOM DROPDOWN ===== */
            .dropdown-header, .dropdown-content {
                background: var(--card-bg);
                border-radius: 8px;
                padding: 10px;
                margin: 5px 0;
                color: var(--text-primary) !important;
            }
            .match-row {
                display: flex;
                justify-content: space-between;
                padding: 8px;
                border-bottom: 1px solid var(--border-color);
            }
            .match-time {
                font-weight: bold;
                color: var(--highlight-color);
            }

            /* ===== FORCE ALL TEXT VISIBLE ===== */
            * {
                color: var(--text-primary) !important;
            }

            /* ===== DARK/LIGHT THEME VARIABLES ===== */
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
                with st.expander(f"🏆 {league_name} ({len(matches)} matches)", expanded=True):
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
        st.markdown(f'<div class="league-subheading">{"📅 Today's Matches"}</div>', unsafe_allow_html=True)

        # Group matches by league
        league_matches = {}
        for league_key in self.leagues.keys():
            matches = self.get_todays_matches(league_key)
            if matches:
                league_matches[league_key] = matches

        # Display matches in dropdowns by league
        for league_key, matches in league_matches.items():
            league_name = self.leagues[league_key]["name"]

            # Create dropdown for each league
            with st.expander(f"{league_name} ({len(matches)} matches)"):
                # Sort matches by time
                matches_sorted = sorted(matches, key=lambda x: x.get('time', '00:00'))

                # Display each match
                for match in matches_sorted:
                    home = match.get('home', 'TBD')
                    away = match.get('away', 'TBD')
                    time = match.get('time', 'TBD')
                    status = match.get('status', '')

                    st.markdown(f"""
                        <div class="match-row">
                            <span class="match-time">{time}</span>
                            <span>{home} - {away}</span>
                            <span>{status}</span>
                        </div>
                    """, unsafe_allow_html=True)

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

    def display_league_selection(self):
        """Display league selection with flag images using Streamlit expander"""

        st.markdown("""
            <style>
            .league-option {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 10px;
                margin: 5px 0;
                border-radius: 6px;
                cursor: pointer;
                color: black
            }
            .league-option:hover {
                background: rgba(30, 60, 114, 0.3);
            }
            .flag-img {
                width: 24px;
                height: 16px;
                object-fit: cover;
                border-radius: 2px;
            }
            </style>
        """, unsafe_allow_html=True)

        selected_league = st.session_state.get('selected_league', list(self.leagues.keys())[3])

        # Folosim expander pentru dropdown effect
        with st.expander(f"🌍 Select League/Season ▼", expanded=False):
            for league_key in self.leagues.keys():
                flag_base64 = self.get_flag_base64(self.leagues[league_key]['flag'])
                col1, col2 = st.columns([1, 20])

                with col1:
                    if flag_base64:
                        st.markdown(f'<img src="data:image/png;base64,{flag_base64}" class="flag-img">',
                                    unsafe_allow_html=True)
                    else:
                        st.write("🏳️")

                with col2:
                    if st.button(self.leagues[league_key]['name'], key=f"btn_{league_key}", use_container_width=True):
                        selected_league = league_key
                        st.session_state.selected_league = league_key
                        st.rerun()

        return selected_league, self.leagues[selected_league]

    def build_team_league_map(self):
        """
        Creează mapping automat echipă → ligă folosind fișierele -clean.csv din processed.
        """
        team_league_map = {}

        for league_key, league_info in self.leagues.items():
            clean_file = f"processed/standings-with-matches-{league_key}-clean.csv"
            if os.path.exists(clean_file):
                try:
                    df = pd.read_csv(clean_file)
                    if "home_team" in df.columns and "away_team" in df.columns:
                        teams = set(df["home_team"]).union(set(df["away_team"]))
                        for team in teams:
                            # Dacă echipa nu e deja mapată, o adăugăm
                            if team not in team_league_map:
                                team_league_map[team] = league_key
                except Exception as e:
                    st.warning(f"Eroare la citirea {clean_file}: {e}")

        return team_league_map

    def download_league_data(self, selected_league, league_info):
        """Download data for selected league if not exists"""
        standings_file_json = f"processed/standings-{selected_league}.json"
        matches_file_json = f"processed/all-matches-{selected_league}.json"
        fixtures_file_json = f"processed/fixtures-{selected_league}.json"
        winrate_file_csv = f"processed/standings-with-winrate-features-{selected_league}.csv"

        # === SPECIAL CASE: Champions League 2024-2025 ===
        if selected_league == "champions-league-2024-2025":
            cl_file = "processed/standings-with-winrate-features-champions-league-2024-2025.csv"

            if not os.path.exists(cl_file):
                st.error("Fișierul Champions League 2024-2025 nu există. Rulează procesarea manuală din main.")
                return None, None, None, None

            cl_df = pd.read_csv(cl_file)

            # Extragem echipele participante
            teams = set(cl_df["home_team"]).union(set(cl_df["away_team"]))

            # Construim automat mapping echipă → ligă
            league_map = self.build_team_league_map()

            # Încărcăm ligile echipelor participante
            league_dfs = []
            for team in teams:
                league_name = league_map.get(team)
                if league_name:
                    path = f"processed/standings-with-winrate-features-{league_name}.csv"
                    if os.path.exists(path):
                        league_dfs.append(pd.read_csv(path))

            # Combinăm Champions League + ligile naționale
            if league_dfs:
                all_data = pd.concat([cl_df] + league_dfs, ignore_index=True)
            else:
                all_data = cl_df

            combined_file = "processed/champions-league-2024-2025-combined.csv"
            all_data.to_csv(combined_file, index=False, encoding="utf-8-sig")

            st.success("Datele pentru Champions League au fost combinate cu ligile echipelor participante.")
            return None, None, None, combined_file

        # === SPECIAL CASE: Champions League 2025-2026 - folosește sezonul anterior ===
        if selected_league == "champions-league-2025-2026":
            previous_season = "champions-league-2024-2025"
            previous_winrate_file = f"processed/standings-with-winrate-features-{previous_season}.csv"

            if not os.path.exists(previous_winrate_file):
                st.warning(f"Need data from previous season ({previous_season}) for predictions")
                previous_standings = f"processed/standings-{previous_season}.json"
                previous_matches = f"processed/all-matches-{previous_season}.json"

                if not os.path.exists(previous_standings):
                    st.info(f"Downloading previous season standings: {previous_season}")
                    if previous_season in self.leagues:
                        scrape_and_save_standings(self.leagues[previous_season]["standings_url"], previous_standings)

                if not os.path.exists(previous_matches):
                    st.info(f"Downloading previous season matches: {previous_season}")
                    if previous_season in self.leagues:
                        scrape_and_save_matches(self.leagues[previous_season]["results_url"], previous_matches)

                if os.path.exists(previous_standings) and os.path.exists(previous_matches):
                    st.info("Processing previous season data...")
                    processor = StandingsProcessor(previous_standings, previous_matches)
                    processor.flatten_to_long().clean_eda()
                    cleaned_csv = f"processed/standings-with-matches-{previous_season}-clean.csv"
                    processor.save_csv(cleaned_csv)

                    preprocessor = MatchPreprocessor(cleaned_csv)
                    preprocessor.load_csv() \
                        .fill_missing(0) \
                        .convert_numeric_and_percentage() \
                        .split_goals_column() \
                        .drop_zero_heavy_columns() \
                        .normalize_large_stats() \
                        .save_csv(f"processed/standings-with-matches-{previous_season}-cleaned.csv")

                    ff = FootballWinRateFeatures(cleaned_csv)
                    ff.encode_columns().create_winrate_features(N_recent=10).save_csv(previous_winrate_file)

            if "fixtures_url" in league_info and league_info["fixtures_url"] and not os.path.exists(fixtures_file_json):
                st.info("Downloading Champions League fixtures...")
                scrape_and_save_fixtures(league_info["fixtures_url"], fixtures_file_json)

            return None, None, fixtures_file_json, previous_winrate_file

        # === Normal flow pentru alte ligi ===
        if not os.path.exists(standings_file_json):
            st.info("Downloading standings...")
            scrape_and_save_standings(league_info["standings_url"], standings_file_json)

        if not os.path.exists(matches_file_json):
            st.info("Downloading results...")
            scrape_and_save_matches(league_info["results_url"], matches_file_json)

        if "fixtures_url" in league_info and not os.path.exists(fixtures_file_json):
            st.info("Downloading fixtures...")
            scrape_and_save_fixtures(league_info["fixtures_url"], fixtures_file_json)

        if not os.path.exists(winrate_file_csv):
            st.info("Processing data and creating winrate features...")
            processor = StandingsProcessor(standings_file_json, matches_file_json)
            processor.flatten_to_long().clean_eda()
            cleaned_csv = f"processed/standings-with-matches-{selected_league}-clean.csv"
            processor.save_csv(cleaned_csv)

            preprocessor = MatchPreprocessor(cleaned_csv)
            preprocessor.load_csv() \
                .fill_missing(0) \
                .convert_numeric_and_percentage() \
                .split_goals_column() \
                .drop_zero_heavy_columns() \
                .normalize_large_stats() \
                .save_csv(f"processed/standings-with-matches-{selected_league}-cleaned.csv")
            preprocessed_csv = f"processed/standings-with-matches-{selected_league}-clean.csv"

            ff = FootballWinRateFeatures(preprocessed_csv)
            ff.encode_columns().create_winrate_features(N_recent=10).save_csv(winrate_file_csv)

        return standings_file_json, matches_file_json, fixtures_file_json, winrate_file_csv

    def display_league_data(self, selected_league, standings_file_json, matches_file_json, fixtures_file_json):
        """Display league data with dropdown sections"""
        league_info = self.leagues[selected_league]
        st.markdown(f'<div class="league-title">{league_info["name"]}</div>', unsafe_allow_html=True)

        # Standings section with dropdown - doar dacă există date
        with st.expander("🏆 Standings", expanded=False):
            if standings_file_json and os.path.exists(standings_file_json):
                with open(standings_file_json, "r", encoding="utf-8") as f:
                    standings_data = json.load(f)
                df_standings = pd.json_normalize(standings_data["standings"])
                st.dataframe(df_standings)
            else:
                st.write("No standings data available for this season")

        # Results section with dropdown - doar dacă există date
        with st.expander("📊 Results", expanded=False):
            if matches_file_json and os.path.exists(matches_file_json):
                with open(matches_file_json, "r", encoding="utf-8") as f:
                    matches_data = json.load(f)
                df_results = pd.json_normalize(matches_data["matches"])
                if not df_results.empty:
                    display_cols = ["date", "home", "away", "home_goals", "away_goals", "status"]
                    st.dataframe(df_results[display_cols])
                else:
                    st.write("No results data available")
            else:
                st.write("No results data available for this season")

        # Fixtures section with dropdown
        with st.expander("📅 Upcoming Fixtures", expanded=False):
            if fixtures_file_json and os.path.exists(fixtures_file_json):
                with open(fixtures_file_json, "r", encoding="utf-8") as f:
                    fixtures_data = json.load(f)
                df_fixtures = pd.json_normalize(fixtures_data["matches"])
                if not df_fixtures.empty:
                    display_cols = ["date", "home", "away", "time", "status"]
                    df_display_fixtures = df_fixtures.copy()
                    for col in display_cols:
                        if col not in df_display_fixtures.columns:
                            df_display_fixtures[col] = ""
                    st.dataframe(df_display_fixtures[display_cols])
                else:
                    st.write("No fixtures data available")
            else:
                st.write("No fixtures data available for this season")

    def get_future_matches(self, matches_file_json, fixtures_file_json):
        """Get future matches from results and fixtures"""
        df_results = pd.DataFrame()
        df_fixtures = pd.DataFrame()

        if matches_file_json and os.path.exists(matches_file_json):
            with open(matches_file_json, "r", encoding="utf-8") as f:
                matches_data = json.load(f)
            df_results = pd.json_normalize(matches_data["matches"])

        if fixtures_file_json and os.path.exists(fixtures_file_json):
            with open(fixtures_file_json, "r", encoding="utf-8") as f:
                fixtures_data = json.load(f)
            df_fixtures = pd.json_normalize(fixtures_data["matches"])

        # Combine future matches
        future_matches = pd.DataFrame()
        if not df_results.empty:
            future_results = df_results[df_results["status"] == "NOT STARTED"]
            future_matches = pd.concat([future_results, df_fixtures], ignore_index=True)
        elif not df_fixtures.empty:
            future_matches = df_fixtures

        return future_matches

    def display_prediction_section(self, selected_league, winrate_file_csv, future_matches):
        """Display prediction section with dropdown"""
        if "2024-2025" in selected_league or "2025-2026" in selected_league:
            with st.expander("⚽ Predict Future Match", expanded=False):

                # Verifică dacă fișierul winrate există
                if not os.path.exists(winrate_file_csv):
                    st.warning("Prediction data not available for this season. Please select another league.")
                    return

                if future_matches is None or future_matches.empty:
                    st.info("No future matches available for prediction.")
                    return

                future_matches["match_str"] = future_matches.apply(
                    lambda x: f"{x['home']} - {x['away']} on {x['date']} {x.get('time', '')}", axis=1
                )

                selected_match = st.selectbox(
                    "Select a match",
                    future_matches["match_str"],
                    key="match_select"
                )

                if st.button("Predict"):
                    with st.spinner("Generating predictions... This may take a few moments."):
                        try:
                            predictor = FootballMatchPredictor([winrate_file_csv])
                            predictor.train_models()

                            home_team, away_team = selected_match.split(" - ")[0], \
                                selected_match.split(" - ")[1].split(" on ")[0]

                            date_time_str = selected_match.split(" on ")[1].strip()
                            parts = date_time_str.split()
                            date_obj = datetime.strptime(parts[0], "%d.%m.%Y")
                            date_formatted = date_obj.strftime("%Y-%m-%d")
                            time_part = parts[1] if len(parts) > 1 else "00:00"

                            predictions = predictor.predict_future_match(
                                date=date_formatted,
                                time=time_part,
                                home_team=home_team,
                                away_team=away_team
                            )

                            # VERIFICĂ DACĂ PREDICȚIA A REUȘIT
                            if not predictions or predictions.get('score') is None:
                                st.error(
                                    "Could not generate prediction for this match. The teams may not have sufficient historical data.")
                                return

                        except Exception as e:
                            st.error(f"Prediction failed: {str(e)}")
                            return

                    # Match result display (similar to live scores)
                    st.markdown(f"""
                        <div style="
                            background: linear-gradient(45deg, #1E3C72, #2A5298);
                            color: white;
                            padding: 15px;
                            border-radius: 12px;
                            margin: 15px 0;
                            border: 2px solid #E6DFB2;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="flex: 2; font-weight: bold; font-size: 18px; text-align: left;">
                                    {home_team}
                                </div>
                                <div style="flex: 1; font-weight: bold; font-size: 24px; text-align: center; color: #E6DFB2;">
                                    {predictions.get('score', '0:0').split(':')[0]} - {predictions.get('score', '0:0').split(':')[1]}
                                </div>
                                <div style="flex: 2; font-weight: bold; font-size: 18px; text-align: right;">
                                    {away_team}
                                </div>
                            </div>
                            <div style="text-align: center; font-size: 14px; color: #E6DFB2; margin-top: 8px;">
                                {date_time_str} • Predicted Score
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"**Total Goals:** {predictions.get('goals', 0)}")

                    # Outcome probabilities chart
                    outcome_idx, probs = predictions.get("outcome", (0, [0.33, 0.34, 0.33]))
                    prob_df = pd.DataFrame({
                        "Team": [home_team, "Draw", away_team],
                        "Probability (%)": [probs[1] * 100, probs[0] * 100, probs[2] * 100]
                    })

                    chart = alt.Chart(prob_df).mark_bar(size=50).encode(
                        x=alt.X('Team:N', sort=[home_team, 'Draw', away_team], title=None),
                        y=alt.Y('Probability (%):Q', title='Probability (%)'),
                        color=alt.Color(
                            'Probability (%):Q',
                            scale=alt.Scale(
                                domain=[prob_df['Probability (%)'].min(), prob_df['Probability (%)'].max()],
                                range=['#FFFFCC', '#FFFF99', '#FFB266', '#FF9933', '#FF0000', '#CC0000']
                            ),
                            legend=None
                        ),
                        tooltip=['Team', 'Probability (%)']
                    ).properties(
                        width=100,
                        height=400,
                        title='Match Outcome Probabilities',
                    )

                    text = alt.Chart(prob_df).mark_text(
                        align='center',
                        baseline='middle',
                        dy=-15,
                        fontSize=14,
                        fontWeight='bold',
                        color='#A0A0A0'
                    ).encode(
                        x=alt.X('Team:N', sort=[home_team, 'Draw', away_team]),
                        y=alt.Y('Probability (%):Q'),
                        text=alt.Text('Probability (%):Q', format='.1f')
                    )

                    final_chart = chart + text
                    st.altair_chart(final_chart, use_container_width=True)

                    # Stats table
                    stats = predictions.get("stats", {})
                    df_stats = pd.DataFrame(stats).T.rename(index={"home": home_team, "away": away_team})
                    st.subheader("📈 Predicted Match Stats")
                    st.dataframe(df_stats.style.format("{:.2f}").highlight_max(axis=1, color="#B2C4E2"))

    def run(self):
        """Main method to run the app"""
        # Display today's matches
        self.display_todays_matches()
        # Display live scores from API
        self.display_live_scores_from_api()

        # League selection
        selected_league, league_info = self.display_league_selection()

        # Download data
        standings_file_json, matches_file_json, fixtures_file_json, winrate_file_csv = self.download_league_data(
            selected_league, league_info
        )

        # Display league data with dropdowns
        self.display_league_data(selected_league, standings_file_json, matches_file_json, fixtures_file_json)

        # Get future matches
        future_matches = self.get_future_matches(matches_file_json, fixtures_file_json)

        # Display prediction section
        self.display_prediction_section(selected_league, winrate_file_csv, future_matches)


# Run the app
if __name__ == "__main__":
    app = FootballXApp()
    app.run()