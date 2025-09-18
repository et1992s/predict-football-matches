import os
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class LiveScoreService:
    def __init__(self):
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        self.host = "v3.football.api-sports.io"

    def get_games_widget(self, league_id: str = "", season: str = "", date: str = "") -> str:
        """Returnează HTML pentru widget-ul 'Games'"""
        return f"""
        <div id="wg-api-football-games"
             data-host="{self.host}"
             data-key="{self.api_key}"
             data-date="{date}"
             data-league="{league_id}"
             data-season="{season}"
             data-theme="dark"
             data-refresh="15"
             data-show-toolbar="true"
             data-show-errors="false"
             data-show-logos="true"
             data-modal-game="true"
             data-modal-standings="true"
             data-modal-show="true"
             data-modal-prefix="wg-api-football"
             class="wg_loader">
        </div>
        <script type="module" src="https://widgets.api-sports.io/2.0.3/widgets.js"></script>
        """

    def get_standings_widget(self, league_id: str, season: str) -> str:
        """Returnează HTML pentru widget-ul 'Standings'"""
        return f"""
        <div id="wg-api-football-standings"
             data-host="{self.host}"
             data-key="{self.api_key}"
             data-league="{league_id}"
             data-season="{season}"
             data-theme="dark"
             data-show-errors="false"
             data-show-logos="true"
             class="wg_loader">
        </div>
        <script type="module" src="https://widgets.api-sports.io/2.0.3/widgets.js"></script>
        """

    def display_widget(self, widget_html: str, height: int = 600):
        """Afișează widget-ul în Streamlit"""
        components.html(widget_html, height=height, scrolling=True)
