from standings_scraper import StandingsScraper
from match_scraper import MatchScraper
from concatenate_data import StandingsProcessor
from match_preprocessor import MatchPreprocessor
from win_rate_feature_engineering import FootballWinRateFeatures
from match_predictor import FootballMatchPredictor
import os
import json


def scrape_and_save_standings(standings_url, filename):
    scraper = StandingsScraper(standings_url)
    scraper.start()
    data = scraper.scrape()
    scraper.save_json(data, filename)
    scraper.stop()


def scrape_and_save_matches(matches_url, filename):
    scraper = MatchScraper(matches_url, headless=False)
    scraper.start()
    match_ids = scraper.get_all_match_ids()
    print(f"Found {len(match_ids)} matches")
    matches_data = []

    for i, m_id in enumerate(match_ids):
        try:
            match_url = f"https://www.flashscore.com/match/{m_id}/#/match-summary"
            print(f"⏳ Scraping match {i + 1}/{len(match_ids)} -> {match_url}")
            match_detail = scraper.open_match_and_extract(match_url)
            matches_data.append(match_detail.to_dict())
        except Exception as e:
            print(f"❌ Error scraping match {i + 1}: {e}")

    scraper.stop()

    os.makedirs("processed", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"matches": matches_data}, f, ensure_ascii=False, indent=4)
    print(f"Matches saved to {filename}")


def scrape_and_save_fixtures(fixtures_url, filename):
    scraper = MatchScraper(fixtures_url, headless=False)
    scraper.start()
    fixtures_ids = scraper.get_all_match_ids()
    print(f"Found {len(fixtures_ids)} fixtures")

    fixtures_data = []

    for i, m_id in enumerate(fixtures_ids):
        try:
            fixture_url = f"https://www.flashscore.com/match/{m_id}/#/match-summary"
            print(f"⏳ Scraping match {i + 1}/{len(fixtures_ids)} -> {fixture_url}")
            match_detail = scraper.open_match_and_extract(fixture_url)
            fixtures_data.append(match_detail.to_dict())
        except Exception as e:
            print(f"❌ Error scraping match {i + 1}: {e}")

    scraper.stop()

    os.makedirs("processed", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"matches": fixtures_data}, f, ensure_ascii=False, indent=4)
    print(f"Fixtures saved to {filename}")


def main():
    # Campionate: {"nume": (standings_url, results_url, fixtures_url)}
    leagues = {
        "romania-superliga-2024-2025": (
            "https://www.flashscore.com/football/romania/superliga-2024-2025/standings/#/QkBSrPPD/standings/overall/",
            "https://www.flashscore.com/football/romania/superliga-2024-2025/results/",
            None  # nu există fixtures pentru sezonul trecut
        ),
        "romania-superliga-2025-2026": (
            "https://www.flashscore.com/football/romania/superliga/standings/#/02YI7tIj/standings/overall/",
            "https://www.flashscore.com/football/romania/superliga/results/",
            "https://www.flashscore.com/football/romania/superliga/fixtures/"
        ),
        "la-liga-2024-2025": (
            "https://www.flashscore.com/football/spain/laliga-2024-2025/standings/#/dINOZk9Q/standings/overall/",
            "https://www.flashscore.com/football/spain/laliga-2024-2025/results/",
            None
        ),
        "la-liga-2025-2026": (
            "https://www.flashscore.com/football/spain/laliga/standings/#/vcm2MhGk/standings/overall/",
            "https://www.flashscore.com/football/spain/laliga/results/",
            "https://www.flashscore.com/football/spain/laliga/fixtures/"
        ),
        "premier-league-2024-2025": (
            "https://www.flashscore.com/football/england/premier-league-2024-2025/standings/#/lAkHuyP3/standings/overall/",
            "https://www.flashscore.com/football/england/premier-league-2024-2025/results/",
            None
        ),
        "premier-league-2025-2026": (
            "https://www.flashscore.com/football/england/premier-league/standings/#/OEEq9Yvp/standings/overall/",
            "https://www.flashscore.com/football/england/premier-league/results/",
            "https://www.flashscore.com/football/england/premier-league/fixtures/"
        ),
        "bundesliga-2024-2025": (
            "https://www.flashscore.com/football/germany/bundesliga-2024-2025/standings/#/8l1ZdrsC/standings/overall/",
            "https://www.flashscore.com/football/germany/bundesliga-2024-2025/results/",
            None
        ),
        "bundesliga-2025-2026": (
            "https://www.flashscore.com/football/germany/bundesliga/standings/#/8l1ZdrsC/standings/overall/",
            "https://www.flashscore.com/football/germany/bundesliga/results/",
            "https://www.flashscore.com/football/germany/bundesliga/fixtures/"
        ),
        "france-ligue-1-2024-2025": (
            "https://www.flashscore.com/football/france/ligue-1-2024-2025/standings/#/WYO1P5ch/standings/overall/",
            "https://www.flashscore.com/football/france/ligue-1-2024-2025/results/",
            None
        ),
        "france-ligue-1-2025-2026": (
            "https://www.flashscore.com/football/france/ligue-1/standings/#/j9QeTLPP/standings/overall/",
            "https://www.flashscore.com/football/france/ligue-1/results/",
            "https://www.flashscore.com/football/france/ligue-1/fixtures/"
        ),
        "champions-league-2024-2025": (
            "https://www.flashscore.com/football/europe/champions-league-2024-2025/standings/#/2oN82Fw5/standings/overall/",
            "https://www.flashscore.com/football/europe/champions-league-2024-2025/results/",
            None
        ),
        "champions-league-2025-2026": (
            "https://www.flashscore.com/football/europe/champions-league/standings/#/UiRZST3U/standings/overall/",
            "https://www.flashscore.com/football/europe/champions-league/results/",
            "https://www.flashscore.com/football/europe/champions-league/fixtures/"
        ),
        "italy-serie-a-2024-2025": (
            "https://www.flashscore.com/football/italy/serie-a-2024-2025/standings/#/zDpS37lb/standings/overall/",
            "https://www.flashscore.com/football/italy/serie-a-2024-2025/results/",
            None
        ),
        "italy-serie-a-2025-2026": (
            "https://www.flashscore.com/football/italy/serie-a/standings/#/6PWwAsA7/live-standings/",
            "https://www.flashscore.com/football/italy/serie-a/results/",
            "https://www.flashscore.com/football/italy/serie-a/fixtures/"
        ),
        "netherlands-eredivisie-2024-2025": (
            "https://www.flashscore.com/football/netherlands/eredivisie-2024-2025/standings/#/KCMrEcSo/standings/overall/",
            "https://www.flashscore.com/football/netherlands/eredivisie-2024-2025/results/",
            None
        ),
        "netherlands-eredivisie-2025-2026": (
            "https://www.flashscore.com/football/netherlands/eredivisie/standings/#/dWKtjvdd/standings/overall/",
            "https://www.flashscore.com/football/netherlands/eredivisie/results/",
            "https://www.flashscore.com/football/netherlands/eredivisie/fixtures/"
        ),
        "liga-portugal-2024-2025": (
            "https://www.flashscore.com/football/portugal/liga-portugal-2024-2025/standings/#/0d7EBBWo/standings/overall/",
            "https://www.flashscore.com/football/portugal/liga-portugal-2024-2025/results/",
            None
        ),
        "liga-portugal-2025-2026": (
            "https://www.flashscore.com/football/portugal/liga-portugal/standings/#/IgF19YCc/live-standings/",
            "https://www.flashscore.com/football/portugal/liga-portugal/results/",
            "https://www.flashscore.com/football/portugal/liga-portugal/fixtures/"
        ),
        "jupiler-pro-league-2024-2025": (
            "https://www.flashscore.com/football/belgium/jupiler-pro-league-2024-2025/standings/#/v7MrIGpM/standings/overall/",
            "https://www.flashscore.com/football/belgium/jupiler-pro-league-2024-2025/results/",
            None
        ),
        "jupiler-pro-league-2025-2026": (
            "https://www.flashscore.com/football/belgium/jupiler-pro-league/standings/#/WbIIL8v0/live-standings/",
            "https://www.flashscore.com/football/belgium/jupiler-pro-league/results/",
            "https://www.flashscore.com/football/belgium/jupiler-pro-league/fixtures/"
        )
        # poți adăuga și alte campionate aici
    }

    winrate_files = []

    for league, (standings_url, results_url, fixtures_url) in leagues.items():
        print(f"\n=== PIPELINE {league.upper()} ===")

        standings_file = f"processed/standings-{league}.json"
        matches_file = f"processed/all-matches-{league}.json"
        fixtures_file = f"processed/fixtures-{league}.json"

        if "champions-league-2025-2026" in league:
            print(f"skipping standings and matches for {league}")

            if fixtures_url and not os.path.exists(fixtures_file):
                scrape_and_save_fixtures(fixtures_url, fixtures_file)
                print(f"Fixtures saved to {fixtures_file}")

            continue

        # 1. Scrape standings dacă nu există deja
        if not os.path.exists(standings_file):
            scrape_and_save_standings(standings_url, standings_file)

        # 1b. Scrape results dacă nu există deja
        if not os.path.exists(matches_file):
            scrape_and_save_matches(results_url, matches_file)

        # 1c. Scrape fixtures dacă există URL și nu există fișier
        if fixtures_url and not os.path.exists(fixtures_file):
            scrape_and_save_fixtures(fixtures_url, fixtures_file)

        # 2. Flatten + clean
        processor = StandingsProcessor(standings_file, matches_file)
        processor.flatten_to_long().clean_eda()
        cleaned_csv = f"processed/standings-with-matches-{league}-clean.csv"
        processor.save_csv(cleaned_csv)

        # 3. Preprocess
        preprocessor = MatchPreprocessor(cleaned_csv)
        preprocessor.load_csv() \
            .fill_missing(0) \
            .convert_numeric_and_percentage() \
            .split_goals_column() \
            .drop_zero_heavy_columns() \
            .normalize_large_stats() \
            .save_csv(f"processed/standings-with-matches-{league}-cleaned.csv")
        preprocessed_csv = f"processed/standings-with-matches-{league}-clean.csv"

        # 4. Winrate features
        ff = FootballWinRateFeatures(preprocessed_csv)
        ff.encode_columns().create_winrate_features(N_recent=5) \
            .save_csv(f"processed/standings-with-winrate-features-{league}.csv")
        winrate_files.append(f"processed/standings-with-winrate-features-{league}.csv")

    # 5. Train modele
    predictor = FootballMatchPredictor(winrate_files)
    predictor.train_models()

    # 6. Testăm toate modelele și salvăm CSV cu y_test vs y_pred
    csv_test_path = "processed/all_predictions.csv"
    predictor.test_all_models_and_save(test_size=0.3, csv_path=csv_test_path)
    print(f"\nCSV-ul cu predicții vs ground truth a fost salvat aici: {csv_test_path}")

    # 7. Interactive prediction doar pentru sezonul curent 2025-2026
    current_season = "romania-superliga-2025-2026"
    print("\n=== PREDICȚIE MECI VIITOR - SEZON 2025-2026 ===")
    while True:
        date = input("Data (YYYY-MM-DD): ").strip()
        time = input("Ora (HH:MM): ").strip()
        home_team = input("Echipa gazdă: ").strip()
        away_team = input("Echipa oaspete: ").strip()

        predictions = predictor.predict_future_match(date, time, home_team, away_team)
        if predictions:
            print("\nRezultatele au fost salvate și în predictions_log.csv")

        cont = input("\nVrei să introduci alt meci? (da/nu): ").strip().lower()
        if cont != 'da':
            print("La revedere!")
            break


if __name__ == "__main__":
    main()
