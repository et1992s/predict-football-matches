from playwright.sync_api import sync_playwright
import json
import os

class StandingsScraper:
    def __init__(self, url, headless=True):
        self.URL = url
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        self.page.goto(self.URL)
        self.accept_cookies()
        self.page.wait_for_selector("div.ui-table__row", timeout=10000)

    def stop(self):
        try: self.browser.close()
        except: pass
        try: self.playwright.stop()
        except: pass

    def accept_cookies(self):
        try:
            self.page.locator("#onetrust-accept-btn-handler").click(timeout=10000)
        except:
            try:
                self.page.locator("button:has-text('Accept All')").click(timeout=10000)
            except:
                pass

    def scrape(self):
        data = []
        rows = self.page.locator("div.ui-table__row")
        for i in range(rows.count()):
            row = rows.nth(i)
            try:
                rank = row.locator("div.tableCellRank").inner_text().strip()
                team = row.locator("a.tableCellParticipant__name").inner_text().strip()
                values = row.locator("span.table__cell--value")
                if values.count() >= 7:
                    MP = values.nth(0).inner_text().strip()
                    W = values.nth(1).inner_text().strip()
                    D = values.nth(2).inner_text().strip()
                    L = values.nth(3).inner_text().strip()
                    GF, GA = values.nth(4).inner_text().strip().split(":")
                    GD = values.nth(5).inner_text().strip()
                    Pts = values.nth(6).inner_text().strip()
                    form_icons = row.locator("div.table__cell--form a.tableCellFormIcon")
                    Form = "".join([form_icons.nth(j).locator("span").inner_text().strip()
                                    for j in range(form_icons.count())])
                    data.append({
                        "rank": rank,
                        "team": team,
                        "MP": MP, "W": W, "D": D, "L": L,
                        "GF": GF, "GA": GA, "GD": GD, "Pts": Pts,
                        "Form": Form
                    })
            except Exception as e:
                print(f"Skipping row {i}: {e}")
        return data

    def save_json(self, data, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({"standings": data}, f, ensure_ascii=False, indent=4)
        print(f"Standings saved to '{filename}'")
