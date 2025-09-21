# live_score_scraper.py
import json
from datetime import datetime
import requests
import streamlit as st


class LiveScoreScraper:
    def __init__(self):
        # ✅ Corect: raw GitHub content URL (nu blob!)
        self.github_url = "https://raw.githubusercontent.com/et1992s/predict-football-matches/master/processed/today_matches.json"
        self.update_interval = 30

    @st.cache_data(ttl=30)
    def load_from_github(_self):
        try:
            response = requests.get(_self.github_url, timeout=10)
            response.raise_for_status()

            data = response.json()
            if not isinstance(data, dict) or "matches" not in data:
                return {"matches": [], "last_update": "", "total_matches": 0}

            return data

        except Exception as e:
            st.error(f"❌ Error loading from GitHub: {e}")
            return {"matches": [], "last_update": "", "total_matches": 0}

    def display_live_scores(self):
        st.markdown('<div class="league-subheading">⚽ Live Scores (Auto-Refresh)</div>', unsafe_allow_html=True)

        with st.spinner("Loading live scores..."):
            data = self.load_from_github()

        matches = data.get("matches", [])

        if not matches:
            st.info("📊 No live matches available\n\nThe system will automatically check every 30 seconds...")
            return

        st.write(f"**🔴 LIVE Matches** ({len(matches)} ongoing)")

        for match in matches:
            self._display_match(match)

        self._display_update_info(data)

    def _display_update_info(self, data):
        last_update = data.get("last_update", "")
        if last_update:
            try:
                update_time = datetime.fromisoformat(last_update)
                time_diff = datetime.now() - update_time
                if time_diff.total_seconds() < 60:
                    st.caption("🕒 Last update: just now")
                elif time_diff.total_seconds() < 300:
                    st.caption("🕒 Last update: a few minutes ago")
                else:
                    st.caption("🕒 Last update: a while ago")
            except:
                pass

    def _display_match(self, match):
        home = match.get('home', 'Unknown')
        away = match.get('away', 'Unknown')
        home_goals = match.get('home_goals', '')
        away_goals = match.get('away_goals', '')
        status = match.get('status', '')
        time_display = match.get('time', '')

        score_display = f"{home_goals} - {away_goals}" if home_goals and away_goals else "-"
        st.markdown(f"**{home}** {score_display} **{away}** ({status or time_display})")

    def run_service(self):
        self.display_live_scores()
        if st.button("🔄 Refresh Now", key="manual_refresh"):
            st.cache_data.clear()
            st.rerun()
