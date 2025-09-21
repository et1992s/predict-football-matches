# live_score_scraper.py
import json
import os
import time
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
        """Încarcă datele de pe GitHub cu fallback local"""
        try:
            response = requests.get(_self.github_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.warning("⚠️ Using local fallback data")
            try:
                if os.path.exists("processed/todays_matches.json"):
                    with open("processed/todays_matches.json", "r", encoding="utf-8") as f:
                        return json.load(f)
            except:
                pass
            return {"matches": [], "last_update": "", "total_matches": 0}

    def display_live_scores(self):
        """Afișează meciurile cu actualizare automată"""
        st.markdown('<div class="league-subheading">⚽ Live Scores (Auto-Refresh)</div>', unsafe_allow_html=True)

        # Loading elegant
        loading_placeholder = st.empty()
        with loading_placeholder:
            with st.spinner("🔄 Loading live scores..."):
                data = self.load_from_github()
        loading_placeholder.empty()

        matches = data.get("matches", [])
        self._setup_auto_refresh()

        if not matches:
            st.info("📊 **No live matches available** - Checking every 30 seconds...")
            return

        st.write(f"**🔴 LIVE Matches** ({len(matches)} ongoing)")

        for match in matches:
            self._display_match(match)

        self._display_update_info(data)

    def _setup_auto_refresh(self):
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()

        elapsed = time.time() - st.session_state.last_refresh
        refresh_in = max(0, self.update_interval - elapsed)

        st.progress(elapsed / self.update_interval, text=f"🔄 Refreshing in {refresh_in:.0f}s")

        if elapsed >= self.update_interval:
            st.session_state.last_refresh = time.time()
            st.rerun()

    def _display_update_info(self, data):
        last_update = data.get("last_update", "")
        if last_update:
            try:
                update_time = datetime.fromisoformat(last_update)
                time_diff = datetime.now() - update_time

                if time_diff.total_seconds() < 60:
                    time_text, color = "just now", "green"
                elif time_diff.total_seconds() < 300:
                    time_text, color = "a few minutes ago", "orange"
                else:
                    time_text, color = "a while ago", "red"

                st.caption(f"🕒 **Last update:** <span style='color:{color}'>{time_text}</span>",
                           unsafe_allow_html=True)
            except:
                pass

    def _display_match(self, match):
        home = match.get('home', 'Unknown')
        away = match.get('away', 'Unknown')
        home_goals = match.get('home_goals', '')
        away_goals = match.get('away_goals', '')
        status = match.get('status', '')
        time_display = match.get('time', '')

        # Verificare scor
        has_score = (home_goals not in ['', None] and away_goals not in ['', None])
        score_display = f"{home_goals} - {away_goals}" if has_score else "-"
        score_style = "color: white; font-weight: bold; font-size: 18px;" if has_score else "color: #95a5a6; font-size: 16px;"

        # Stilare
        is_live = 'LIVE' in str(status).upper() or (time_display and str(time_display).isdigit())

        if is_live:
            bg_color = "linear-gradient(135deg, #ff6b6b, #ee5a24)"
            status_text = f"🔴 LIVE {time_display}'" if time_display else "🔴 LIVE"
            border_style = "border: 2px solid #ff4757;"
        else:
            bg_color = "linear-gradient(135deg, #3498db, #2980b9)"
            status_text = str(status)
            border_style = "border: 1px solid #2980b9;"

        # Afișare
        st.markdown(f"""
                <div style="
                    background: {bg_color};
                    color: white;
                    padding: 12px;
                    border-radius: 10px;
                    margin: 8px 0;
                    {border_style};
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-weight: bold; flex: 2; font-size: 14px;">{home}</div>
                        <div style="{score_style}; flex: 1; text-align: center;">{score_display}</div>
                        <div style="font-weight: bold; flex: 2; text-align: right; font-size: 14px;">{away}</div>
                    </div>
                    <div style="text-align: center; font-size: 12px; margin-top: 8px; font-weight: bold;">
                        {status_text}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    def run_service(self):
        self.display_live_scores()
        if st.button("🔄 Refresh Now", key="manual_refresh"):
            st.cache_data.clear()
            st.session_state.last_refresh = 0
            st.rerun()