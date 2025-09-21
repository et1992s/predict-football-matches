import json
import os
import time

import requests
import streamlit as st
from datetime import datetime
from match_scraper import MatchScraper


class LiveScoreScraper:
    def __init__(self):
        # ✅ CORECT: Adaugă URL-ul GitHub
        self.github_url = "https://github.com/et1992s/predict-football-matches/blob/9e4d921fa8610a7bb53d0f60f3ce007565858578/processed/today_matches.json"
        self.update_interval = 30

    @st.cache_data(ttl=30)
    def load_from_github(_self):
        """Încarcă datele de pe GitHub"""
        try:
            response = requests.get(_self.github_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"❌ Error loading from GitHub: {e}")
            # Fallback la fișierul local
            try:
                if os.path.exists("processed/today_matches.json"):
                    with open("processed/today_matches.json", "r", encoding="utf-8") as f:
                        return json.load(f)
            except:
                pass
            return {"matches": [], "last_update": "", "total_matches": 0}

    def display_live_scores(self):
        """Afișează meciurile cu actualizare automată din GitHub"""
        st.markdown('<div class="league-subheading">⚽ Live Scores (Auto-Refresh)</div>', unsafe_allow_html=True)

        # Indicator de încărcare
        with st.spinner("Loading live scores..."):
            data = self.load_from_github()

        matches = data.get("matches", [])

        # # Auto-refresh logic
        # self._setup_auto_refresh()

        if not matches:
            st.info("""
                📊 **No live matches available**

                The system will automatically check every 30 seconds...
            """)
            return

        # Afișează meciurile
        st.write(f"**🔴 LIVE Matches** ({len(matches)} ongoing)")

        for match in matches:
            self._display_match(match)

        # Afișează info update
        self._display_update_info(data)

    # def _setup_auto_refresh(self):
    #     """Configurează auto-refresh la fiecare 30s"""
    #     current_time = time.time()
    #
    #     # Initializează sau resetează dacă este prea veche
    #     if 'last_refresh' not in st.session_state:
    #         st.session_state.last_refresh = current_time
    #         st.session_state.init_time = current_time
    #
    #     # Resetează dacă sesiunea este prea veche (peste 1 oră)
    #     if current_time - st.session_state.init_time > 3600:
    #         st.session_state.last_refresh = current_time
    #         st.session_state.init_time = current_time
    #
    #     elapsed = current_time - st.session_state.last_refresh
    #
    #     # Asigură-te că progress este între 0 și 1
    #     progress = min(1.0, max(0.0, elapsed / self.update_interval))
    #     refresh_in = max(0, self.update_interval - elapsed)
    #
    #     st.progress(progress, text=f"🔄 Refreshing in {refresh_in:.0f}s")
    #
    #     if elapsed >= self.update_interval:
    #         st.session_state.last_refresh = current_time
    #         st.rerun()

    def _display_update_info(self, data):
        """Afișează informații despre update"""
        last_update = data.get("last_update", "")
        if last_update:
            try:
                update_time = datetime.fromisoformat(last_update)
                time_diff = datetime.now() - update_time

                if time_diff.total_seconds() < 60:
                    time_text = "just now"
                    color = "green"
                elif time_diff.total_seconds() < 300:  # 5 minutes
                    time_text = "a few minutes ago"
                    color = "orange"
                else:
                    time_text = "a while ago"
                    color = "red"

                st.caption(f"🕒 **Last update:** <span style='color:{color}'>{time_text}</span>",
                           unsafe_allow_html=True)
            except:
                pass

    def _display_match(self, match):
        """Afișează un meci"""
        home = match.get('home', 'Unknown')
        away = match.get('away', 'Unknown')
        home_goals = match.get('home_goals', '')
        away_goals = match.get('away_goals', '')
        status = match.get('status', '')
        time_display = match.get('time', '')

        is_live = 'LIVE' in str(status).upper() or (time_display and str(time_display).isdigit())

        if home_goals in ['', None] or away_goals in ['', None]:
            score_display = "-"
            score_style = "color: #95a5a6;"
        else:
            score_display = f"{home_goals} - {away_goals}"
            score_style = "color: white; font-weight: bold;"

        if is_live:
            bg_color = "linear-gradient(135deg, #ff6b6b, #ee5a24)"
            status_text = f"🔴 LIVE {time_display}'"
            border_style = "border: 2px solid #ff4757;"
        else:
            bg_color = "linear-gradient(135deg, #3498db, #2980b9)"
            status_text = str(status)
            border_style = "border: 1px solid #2980b9;"

        st.markdown(f"""
            <div style="
                background: {bg_color};
                color: white;
                padding: 12px;
                border-radius: 10px;
                margin: 8px 0;
                {border_style}
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: bold; flex: 2;">{home}</div>
                    <div style="font-size: 18px; {score_style}; flex: 1; text-align: center;">
                        {score_display}
                    </div>
                    <div style="font-weight: bold; flex: 2; text-align: right;">{away}</div>
                </div>
                <div style="text-align: center; font-size: 12px; margin-top: 8px;">
                    {status_text}
                </div>
            </div>
        """, unsafe_allow_html=True)

    def run_service(self):
        """Rulează serviciul complet"""
        self.display_live_scores()

        # Buton manual de refresh
        if st.button("🔄 Refresh Now", key="manual_refresh"):
            st.cache_data.clear()
            st.session_state.last_refresh = 0  # Force refresh
            st.rerun()
