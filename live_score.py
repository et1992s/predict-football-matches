from datetime import datetime
import requests
import os
from dotenv import load_dotenv

load_dotenv()  # încarcă variabilele din .env

class LiveScoreService:
    def __init__(self):
        self.api_key = os.getenv("API_FOOTBALL_KEY")  # citește cheia din .env
        self.base_url = "https://v3.football.api-sports.io"

    def get_today_live_matches(self):
        """Get only main leagues from each country"""
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
                'Romania': 'Liga 1',
                'Czech-Republic': 'First League',
                'Croatia': 'First Football League',
                'Serbia': 'Super Liga',
                'Ukraine': 'Premier League',
                'Denmark': 'Superliga',
                'Sweden': 'Allsvenskan',
                'Norway': 'Eliteserien',
                'Poland': 'Ekstraklasa'
            }

            uefa_competitions = {'Champions League', 'Europa League', 'Europa Conference League'}

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
