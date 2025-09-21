from datetime import datetime
import requests
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # încarcă variabilele din .env

class LiveScoreService:
    def __init__(self):
        # Citește cheia mai întâi din st.secrets, apoi din .env
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        self.base_url = "https://v3.football.api-sports.io"

    def get_today_live_matches(self):
        try:
            today = datetime.now().strftime('%Y-%m-%d')

            url = f"{self.base_url}/fixtures"
            params = {'date': today, 'timezone': 'Europe/London'}
            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': 'v3.football.api-sports.io'
            }

            response = requests.get(url, params=params, headers=headers, timeout=15)

            if response.status_code != 200:
                st.write("API Error:", response.status_code, response.text)
                return []

            data = response.json()

            # Ligile principale
            main_leagues = {
                'England': 'Premier League',
                'Spain': 'La Liga',
                'Germany': 'Bundesliga',
                'Italy': 'Serie A',
                'France': 'Ligue 1',
                'Portugal': 'Primeira Liga',
                'Netherlands': 'Eredivisie',
                'Belgium': 'Jupiler Pro League',
                'Scotland': 'Premiership',
                'Turkey': 'Super Lig',
                'Greece': 'Super League',
                'Austria': 'Bundesliga',
                'Switzerland': 'Super League',
                'Romania': 'Liga I',
                'Czech-Republic': 'First League',
                'Croatia': 'First Football League',
                'Serbia': 'Super Liga',
                'Ukraine': 'Premier League',
                'Denmark': 'Superliga',
                'Sweden': 'Allsvenskan',
                'Norway': 'Eliteserien',
                'Poland': 'Ekstraklasa'
            }

            uefa_competitions = {'UEFA Champions League', 'UEFA Europa League', 'UEFA Europa Conference League'}

            live_matches = []
            for fixture in data.get('response', []):
                league_data = fixture['league']
                country = league_data['country']
                league_name = league_data['name']

                is_main_league = (country in main_leagues and league_name == main_leagues[country])
                is_uefa_competition = (league_name in uefa_competitions)

                if is_main_league or is_uefa_competition:
                    fixture_data = fixture['fixture']
                    teams_data = fixture['teams']
                    goals_data = fixture['goals']

                    match_info = {
                        'home': teams_data['home']['name'],
                        'away': teams_data['away']['name'],
                        'home_goals': goals_data['home'],
                        'away_goals': goals_data['away'],
                        'status': fixture_data['status']['short'],
                        'elapsed': fixture_data['status']['elapsed'],
                        'time': fixture_data['date'].split('T')[1][:5],
                        'league': league_name,
                        'country': country,
                        'round': league_data['round'],
                        'fixture_id': fixture_data['id']
                    }
                    live_matches.append(match_info)

            live_matches.sort(key=lambda x: x['country'])
            return live_matches

        except Exception as e:
            print(f"API Error: {e}")
            return []

    def display_live_scores_from_api(self):
        """Display live scores from API-Football"""
        st.markdown(f'<div class="league-subheading">{"Live Scores Today"}</div>', unsafe_allow_html=True)
        try:
            # Inițializează serviciul
            live_service = LiveScoreService()
            live_matches = live_service.get_today_live_matches()

            if not live_matches:
                st.info("Cannot display live scores today, come back tomorrow.")
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
                with st.expander(f"{league_name} ({len(matches)} matches)", expanded=False):
                    for match in matches:
                        self._display_api_match(match)

        except Exception:
            st.error(f"")

    @staticmethod
    def _display_api_match(match):
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
