import time

from playwright.sync_api import sync_playwright


class MatchDetail:
    def __init__(self, date, time_txt, home, away, home_goals, away_goals, status,
                 summary=None, statistics=None, lineups=None):
        self.date = date
        self.time_txt = time_txt
        self.home = home
        self.away = away
        self.home_goals = home_goals
        self.away_goals = away_goals
        self.status = status
        self.summary = summary or []
        self.statistics = statistics or []
        self.lineups = lineups or {}

    def to_dict(self):
        return {
            "date": self.date,
            "time": self.time_txt,
            "home": self.home,
            "away": self.away,
            "home_goals": self.home_goals,
            "away_goals": self.away_goals,
            "status": self.status,
            "summary": self.summary,
            "statistics": self.statistics,
            "lineups": self.lineups
        }

class MatchScraper:
    def __init__(self, matches_url, headless=True):
        self.BASE_URL = matches_url
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless, slow_mo=200)
        self.page = self.browser.new_page()
        self.page.goto(self.BASE_URL, wait_until="domcontentloaded")
        time.sleep(2)

    def stop(self):
        try:
            self.browser.close()
        except:
            pass
        try:
            self.playwright.stop()
        except:
            pass

    def accept_cookies(self):
        try:
            self.page.locator("#onetrust-accept-btn-handler").first.click(timeout=10000)
        except:
            try:
                self.page.locator("button:has-text('Accept All')").first.click(timeout=10000)
            except:
                pass

    # --- Scroll & click "Show more" until all matches are loaded ---
    def load_all_matches(self):
        prev_count = 0
        stable_count = 0
        while True:
            matches = self.page.locator(".event__match")
            count = matches.count()

            # Click "Show more matches" if visible
            try:
                btn = self.page.locator("span:has-text('Show more matches')")
                if btn.count() > 0:
                    btn.first.click(timeout=10000)
                    self.page.wait_for_timeout(10000)
                    continue
            except:
                pass

            # Check if new matches loaded
            if count == prev_count:
                stable_count += 1
                if stable_count >= 3:  # stop if no new matches after 3 scrolls
                    break
            else:
                stable_count = 0
                prev_count = count

            # Scroll down to trigger lazy load
            self.page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            time.sleep(1)

    # --- Extract all match IDs ---
    def get_all_match_ids(self):
        self.load_all_matches()
        matches = self.page.locator(".event__match")
        match_ids = []
        for i in range(matches.count()):
            event_code = matches.nth(i).get_attribute("id")
            if event_code:
                match_ids.append(event_code.split("_")[-1])
        return match_ids

    # --- Extraction helpers ---
    def extract_summary(self, page):
        events = []
        page.wait_for_selector(".smv__participantRow", timeout=10000)
        rows = page.locator(".smv__participantRow")
        row_count = rows.count()

        for i in range(row_count):
            row = rows.nth(i)

            # Minute
            minute = row.locator(".smv__timeBox").first.inner_text().strip() if row.locator(
                ".smv__timeBox").count() else ""

            # Player
            player_locator = row.locator(".smv__playerName div, .smv__playerName")
            player = player_locator.first.inner_text().strip() if player_locator.count() else ""

            # Incident
            incident_locator = row.locator("div[title]")
            incident = incident_locator.first.get_attribute("title").strip() if incident_locator.count() else ""

            events.append({
                "minute": minute,
                "player": player,
                "incident": incident
            })

        return events

    def extract_statistics(self, page):
        stats = []
        blocks = page.locator("div[data-testid='wcl-statistics']")
        for i in range(blocks.count()):
            b = blocks.nth(i)
            label = b.locator("div[data-testid='wcl-statistics-category']").inner_text().strip() if b.locator(
                "div[data-testid='wcl-statistics-category']").count() else ""
            values = b.locator("div[data-testid='wcl-statistics-value']")
            if values.count() >= 2:
                stats.append({
                    "label": label,
                    "home_value": values.nth(0).inner_text().strip(),
                    "away_value": values.nth(1).inner_text().strip()
                })
        return stats

    # --- Scrape upcoming fixtures (matches not yet played) ---
    def extract_fixtures(self):
        self.load_all_matches()
        matches = self.page.locator(".event__match")
        fixtures = []
        for i in range(matches.count()):
            match = matches.nth(i)
            # Date and time
            date_time = ""
            try:
                date_time = match.locator(".event__time").first.inner_text().strip()
            except:
                pass
            date_part, time_part = (date_time.split(" ", 1) if " " in date_time else (date_time, ""))

            # Home and Away teams
            home = match.locator(".event__participant--home").first.inner_text().strip()
            away = match.locator(".event__participant--away").first.inner_text().strip()

            # Create MatchDetail object with default empty scores and status
            fixtures.append(MatchDetail(date_part, time_part, home, away))

        return fixtures

    def extract_formation(self, page):
        formations = {"home_team": "", "away_team": ""}
        try:
            formation_div = page.locator("div[data-testid='wcl-headerSection-text']:has-text('Formation')")
            if formation_div.count():
                spans = formation_div.locator("span")
                if spans.count() >= 3:
                    formations["home_team"] = spans.nth(0).inner_text().strip()
                    formations["away_team"] = spans.nth(2).inner_text().strip()
        except:
            pass
        return formations

    def _extract_players_by_section(self, page, header_text):
        players = {"home_team": [], "away_team": []}
        try:
            headers = page.locator(f"div[data-testid='wcl-headerSection-text']:has-text('{header_text}')")
            for i in range(headers.count()):
                section = headers.nth(i).locator("xpath=following-sibling::div[1]")
                for j in range(
                        section.locator("div.lf__participantNew, div.lf__participantNew.lf__isReversed").count()):
                    p = section.locator("div.lf__participantNew, div.lf__participantNew.lf__isReversed").nth(j)
                    inner_div = p.locator("div[data-testid^='wcl-lineupsParticipantGeneral']")
                    text = ""
                    if inner_div.count():
                        if inner_div.locator("button strong").count():
                            text = inner_div.locator("button strong").first.inner_text().strip()
                        else:
                            text = inner_div.first.inner_text().strip()
                    else:
                        if p.locator("button img").count():
                            text = p.locator("button img").first.get_attribute("alt").strip()
                        else:
                            text = p.inner_text().strip()
                    team_key = "away_team" if "lf__isReversed" in p.get_attribute("class") else "home_team"
                    players[team_key].append(text)
        except:
            pass
        return players

    def extract_starting_lineups(self, page):
        return self._extract_players_by_section(page, "Starting Lineups")

    def extract_substitutes(self, page):
        return self._extract_players_by_section(page, "Substitutes")

    def extract_substituted_players(self, page):
        return self._extract_players_by_section(page, "Substituted players")

    def extract_missing_players(self, page):
        return self._extract_players_by_section(page, "Missing Players")

    def extract_coaches(self, page):
        coaches = {"home_team": "", "away_team": ""}
        try:
            headers = page.locator("div[data-testid='wcl-headerSection-text']:has-text('Coaches')")
            for i in range(headers.count()):
                section = headers.nth(i).locator("xpath=following-sibling::div[1]")
                for j in range(
                        section.locator("div.lf__participantNew, div.lf__participantNew.lf__isReversed").count()):
                    p = section.locator("div.lf__participantNew, div.lf__participantNew.lf__isReversed").nth(j)
                    inner_div = p.locator("div[data-testid^='wcl-lineupsParticipantGeneral']")
                    name = ""
                    if inner_div.count():
                        if inner_div.locator("button strong").count():
                            name = inner_div.locator("button strong").first.inner_text().strip()
                        else:
                            name = inner_div.first.inner_text().strip()
                    else:
                        name = p.inner_text().strip()
                    team_key = "away_team" if "lf__isReversed" in p.get_attribute("class") else "home_team"
                    coaches[team_key] = name
        except:
            pass
        return coaches

    # --- Open match page and extract all data ---
    def open_match_and_extract(self, match_url) -> MatchDetail:
        self.page.goto(match_url, wait_until="domcontentloaded")
        time.sleep(2)

        container = self.page.locator(".duelParticipant__container").first

        date_time = ""
        try:
            date_time = container.locator(".duelParticipant__startTime div").inner_text().strip()
        except:
            pass
        date_part, time_part = (date_time.split(" ", 1) if " " in date_time else (date_time, ""))

        home = container.locator(".duelParticipant__home .participant__participantName a").inner_text()
        away = container.locator(".duelParticipant__away .participant__participantName a").inner_text()

        home_goals = away_goals = ""
        try:
            spans = container.locator(".duelParticipant__score .detailScore__wrapper span").all()
            if len(spans) >= 3:
                home_goals, away_goals = spans[0].inner_text(), spans[2].inner_text()
        except:
            pass

        status = ""
        try:
            status = container.locator(".detailScore__status span").first.inner_text()
        except:
            try:
                status = self.page.locator(".fixedHeaderDuel__detailStatus").first.inner_text()
            except:
                status = ""

        match = MatchDetail(date_part, time_part, home, away, home_goals, away_goals, status)

        # --- Summary tab ---
        try:
            tab_summary = self.page.locator("div[data-testid='wcl-tabs'] button:has-text('Summary')")
            if tab_summary.count():
                tab_summary.first.click()
                self.page.wait_for_selector(".smv__participantRow", timeout=10000)
                match.summary = self.extract_summary(self.page)
        except Exception as e:
            print(f"⚠️ Could not extract summary: {e}")

        # --- Statistics tab ---
        try:
            tab_stats = self.page.locator("div[data-testid='wcl-tabs'] button:has-text('Stats')")
            if tab_stats.count():
                tab_stats.first.click()
                self.page.wait_for_selector("div[data-testid='wcl-statistics']", timeout=10000)
                match.statistics = self.extract_statistics(self.page)
        except Exception as e:
            print(f"⚠️ Could not extract statistics: {e}")

        # --- Lineups ---
        try:
            tab_lineups = self.page.locator("div[data-testid='wcl-tabs'] button:has-text('Lineups')")
            if tab_lineups.count():
                tab_lineups.first.click()
                self.page.wait_for_selector("div.lf__lineUp", timeout=10000)
                match.lineups = {
                    "formation": self.extract_formation(self.page),
                    "starting_lineups": self.extract_starting_lineups(self.page),
                    "substitutes": self.extract_substitutes(self.page),
                    "substituted_players": self.extract_substituted_players(self.page),
                    "missing_players": self.extract_missing_players(self.page),
                    "coaches": self.extract_coaches(self.page)
                }
        except Exception as e:
            print(f"⚠️ Could not extract lineups: {e}")

        return match
