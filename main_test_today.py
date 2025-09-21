import json
import os

from match_scraper import MatchScraper


def main():
    # Folosește URL-ul specific ligii
    league_url = "https://www.flashscore.com/football/colombia/primera-a/#/Oj4yELnn/live-standings/"
    scraper = MatchScraper(league_url, headless=False)
    scraper.start()

    print("🔎 Extracting matches from Canadian Premier League...")
    matches_data = scraper.extract_today_matches([])

    # Verifică dacă există date invalide
    invalid_data = any("---" in match["home"] or "---" in match["away"] for match in matches_data)

    if invalid_data:
        print("❌ Invalid data detected in extracted matches!")
        print("🛑 Closing browser due to data quality issues")
        scraper.stop()
        return  # Ieși din funcție fără a salva datele

    # Debug: afișăm fiecare meci extras
    for match in matches_data:
        print(
            f"⚽ {match['home']} vs {match['away']} | Status: {match['status']} | Scor: {match['home_goals']}-{match['away_goals']}")

    scraper.stop()

    os.makedirs("processed", exist_ok=True)
    filename = "processed/today_matches.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"matches": matches_data}, f, ensure_ascii=False, indent=4)

    print(f"✅ Extracted {len(matches_data)} matches")
    print(f"📂 Saved to {filename}")


if __name__ == "__main__":
    main()