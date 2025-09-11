import json
import pandas as pd
import re

class StandingsProcessor:
    def __init__(self, standings_file, matches_file):
        self.standings_file = standings_file
        self.matches_file = matches_file
        self.df = None

    @staticmethod
    def load_json(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def normalize_stat_name(name: str) -> str:
        name = name.strip()
        name = re.sub(r"[\s\(\)%]+", "_", name)
        return name.strip("_")

    @staticmethod
    def outcome(goals_for, goals_against):
        if goals_for > goals_against:
            return "W"
        elif goals_for < goals_against:
            return "L"
        else:
            return "D"

    def flatten_to_long(self):
        standings_data = self.load_json(self.standings_file)["standings"]
        matches_data = self.load_json(self.matches_file)

        if isinstance(matches_data, dict) and "matches" in matches_data:
            matches_data = matches_data["matches"]

        team_rank_map = {team["team"]: team["rank"] for team in standings_data}
        flattened_rows = []

        for team in standings_data:
            team_name = team["team"]
            team_matches = [m for m in matches_data if m.get("home") == team_name or m.get("away") == team_name]
            team_matches.sort(key=lambda x: (x.get("date", ""), x.get("time", "")))

            for match in team_matches:
                is_home = match.get("home") == team_name
                opponent = match.get("away") if is_home else match.get("home")

                try:
                    goals_for = int(match.get("home_goals") if is_home else match.get("away_goals"))
                    goals_against = int(match.get("away_goals") if is_home else match.get("home_goals"))
                except:
                    goals_for = goals_against = 0

                row = {
                    "Rank": team["rank"],
                    "Team": team_name,
                    "Wins": team["W"],
                    "Draws": team["D"],
                    "Loses": team["L"],
                    "Team_goals": team["GF"],
                    "Opponents_goals": team["GA"],
                    "Goal_difference": team["GD"],
                    "Points": team["Pts"],
                    "Opponent": opponent,
                    "opponent_rank": team_rank_map.get(opponent, ""),
                    "Date": match.get("date", ""),
                    "Time": match.get("time", ""),
                    "Home/Away": "home" if is_home else "away",
                    "team_goals": goals_for,
                    "opponent_goals": goals_against,
                    "Outcome": self.outcome(goals_for, goals_against),
                    "Target_Winner": (
                        "team" if goals_for > goals_against else
                        "opponent" if goals_for < goals_against else
                        "draw"
                    )
                }

                for stat in match.get("statistics", []):
                    stat_name = self.normalize_stat_name(stat["label"])
                    stat_home, stat_away = stat["home_value"], stat["away_value"]

                    if is_home:
                        row[f"stat_{stat_name}_team"] = stat_home
                        row[f"stat_{stat_name}_opponent"] = stat_away
                    else:
                        row[f"stat_{stat_name}_team"] = stat_away
                        row[f"stat_{stat_name}_opponent"] = stat_home

                flattened_rows.append(row)

        self.df = pd.DataFrame(flattened_rows)
        return self

    def clean_eda(self):
        if self.df is None:
            raise ValueError("Dataframe is empty. Call flatten_to_long() first.")
        df_clean = self.df.copy()

        for col in df_clean.columns:
            if df_clean[col].astype(str).str.contains("%").any():
                df_clean[col] = (
                    df_clean[col]
                    .astype(str)
                    .str.replace(",", ".")
                    .str.extract(r"(\d+\.?\d*)")
                    .astype(float)
                    / 100.0)

            df_clean[col] = pd.to_numeric(df_clean[col], errors="ignore")

        self.df = df_clean.fillna(0)
        return self

    def save_csv(self, output_csv: str):
        if self.df is None:
            raise ValueError("Dataframe is empty. Nothing to save.")
        self.df.to_csv(output_csv, index=False, encoding="utf-8")
        print(f"CSV salvat în {output_csv}")
        return self
