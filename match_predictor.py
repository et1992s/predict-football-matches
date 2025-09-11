import os
import warnings
from datetime import datetime

import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore')


class FootballMatchPredictor:
    def __init__(self, csv_paths: list):
        dfs = []
        for path in csv_paths:
            try:
                df = pd.read_csv(path)
                dfs.append(df)
                print(f"Încărcat: {path} ({len(df)} meciuri)")
            except FileNotFoundError:
                print(f"Fișierul {path} nu a fost găsit")
                continue
            except Exception as e:
                print(f"Eroare la încărcarea {path}: {e}")
                continue

        if not dfs:
            raise ValueError("Niciun fișier CSV nu a putut fi încărcat")

        self.df = pd.concat(dfs, ignore_index=True)
        print(f"📊 Dataset total: {len(self.df)} meciuri")

        self.team_encoder = LabelEncoder()
        self.scalers = {}
        self.models = {}

        self.all_features = [
            'win_rate_global', 'win_rate_lastN', 'home_win_rate', 'away_win_rate',
            'h2h_win_rate', 'form_score', 'goal_diff_win_rate', 'weighted_outcome',
            'team_goals', 'opponent_goals', 'Rank', 'opponent_rank', 'Home_encoded']

        self.stat_features = [
            'stat_Expected_Goals_xG_team', 'stat_Expected_Goals_xG_opponent',
            'stat_Ball_Possession_team', 'stat_Ball_Possession_opponent',
            'stat_Total_shots_team', 'stat_Total_shots_opponent',
            'stat_Shots_on_target_team', 'stat_Shots_on_target_opponent',
            'stat_Corner_Kicks_team', 'stat_Corner_Kicks_opponent',
            'stat_Yellow_Cards_team', 'stat_Yellow_Cards_opponent',
            'stat_Red_Cards_team', 'stat_Red_Cards_opponent',
            'stat_Passes_team', 'stat_Passes_opponent',
            'stat_Fouls_team', 'stat_Fouls_opponent',
            'stat_Tackles_team', 'stat_Tackles_opponent',
            'Wins', 'Draws', 'Loses', 'Team_goals',
            'Opponents_goals', 'Goal_difference', 'Points']

        self.all_features.extend(self.stat_features)
        self.df['total_goals'] = self.df['team_goals'] + self.df['opponent_goals']
        self.df['goals_class'] = self.df['total_goals'].apply(lambda x: min(int(x), 6))
        self.df["score_class"] = self.df.apply(
            lambda row: f"{min(row['team_goals'], 5)}:{min(row['opponent_goals'], 5)}", axis=1)

        if "Date" in self.df.columns:
            self.df["Date"] = pd.to_datetime(self.df["Date"], dayfirst=True, errors='coerce').dt.date
        if "Time" in self.df.columns:
            self.df["Time"] = pd.to_datetime(self.df["Time"], format="%H:%M", errors='coerce').dt.time

        self._clean_data()

        all_teams = pd.concat([self.df["Team"], self.df["Opponent"]]).unique()
        self.team_encoder.fit(all_teams)
        self.df["Team_encoded"] = self.team_encoder.transform(self.df["Team"])
        self.df["Opponent_encoded"] = self.team_encoder.transform(self.df["Opponent"])

        self.df["Outcome_encoded"] = self.df.apply(
            lambda row: 1 if row["team_goals"] > row["opponent_goals"]
            else 2 if row["team_goals"] < row["opponent_goals"]
            else 0, axis=1)

        if 'Home_encoded' not in self.df.columns:
            self.df['Home_encoded'] = self.df['Home/Away'].apply(
                lambda x: 1 if x == 'Home' else 0)

    def _clean_data(self):
        print("Curățarea datelor...")

        numeric_features = self.all_features + self.stat_features
        for feature in numeric_features:
            if feature in self.df.columns:
                if self.df[feature].dtype in ['int64', 'float64']:
                    mean_val = self.df[feature].mean()
                    self.df[feature] = self.df[feature].fillna(mean_val if not pd.isna(mean_val) else 0)

        critical_columns = ['Team', 'Opponent', 'team_goals', 'opponent_goals']
        self.df = self.df.dropna(subset=critical_columns)

        print(f"Dataset după curățare: {len(self.df)} meciuri")

    def prepare_data(self, target_type='outcome', for_team='home'):
        available_features = [f for f in self.all_features if f in self.df.columns]
        X = self.df[available_features]

        if target_type == 'outcome':
            y = self.df["Outcome_encoded"]
        elif target_type == 'goals':
            y = self.df["goals_class"]
        elif target_type == 'score':
            y = self.df["score_class"]
        else:
            stat_mapping = {
                'corners': 'stat_Corner_Kicks_team' if for_team == 'home' else 'stat_Corner_Kicks_opponent',
                'shots_on_target': 'stat_Shots_on_target_team' if for_team == 'home' else 'stat_Shots_on_target_opponent',
                'possession': 'stat_Ball_Possession_team' if for_team == 'home' else 'stat_Ball_Possession_opponent',
                'yellow_cards': 'stat_Yellow_Cards_team' if for_team == 'home' else 'stat_Yellow_Cards_opponent',
                'fouls': 'stat_Fouls_team' if for_team == 'home' else 'stat_Fouls_opponent',
                'tackles': 'stat_Tackles_team' if for_team == 'home' else 'stat_Tackles_opponent',
                'passes': 'stat_Passes_team' if for_team == 'home' else 'stat_Passes_opponent',
                'shots_total': 'stat_Total_shots_team' if for_team == 'home' else 'stat_Total_shots_opponent',
                'xg': 'stat_Expected_Goals_xG_team' if for_team == 'home' else 'stat_Expected_Goals_xG_opponent'}

            if target_type in stat_mapping:
                y = self.df[stat_mapping[target_type]]
            else:
                raise ValueError(f"Tip țintă necunoscut: {target_type}")
        return X, y

    def train_models(self):
        print("Antrenarea modelelor...")

        self.models = {
            'outcome': RandomForestClassifier(n_estimators=200, random_state=42),
            'goals': RandomForestClassifier(n_estimators=500, random_state=42),
            'score': RandomForestClassifier(n_estimators=500, random_state=42),
        }

        stat_targets = ['corners', 'shots_on_target', 'possession', 'yellow_cards',
                        'fouls', 'tackles', 'passes', 'shots_total', 'xg']

        for target in stat_targets:
            for team_type in ['home', 'away']:
                model_key = f"{target}_{team_type}"
                self.models[model_key] = RandomForestRegressor(n_estimators=200, random_state=42)

        results = {}

        for target_name in ['outcome', 'goals', 'score']:
            print(f"\nAntrenare pentru: {target_name}")

            X, y = self.prepare_data(target_name)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42)

            self.models[target_name].fit(X_train, y_train)
            y_pred = self.models[target_name].predict(X_test)

            accuracy = accuracy_score(y_test, y_pred)
            results[target_name] = {'accuracy': accuracy}

            print(f"Accuracy: {accuracy:.3f}")
            if target_name == 'outcome':
                print(classification_report(y_test, y_pred, zero_division=0))

        for target in stat_targets:
            for team_type in ['home', 'away']:
                print(f"\nAntrenare pentru: {target} ({team_type})")

                X, y = self.prepare_data(target, team_type)
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.3, random_state=42)

                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)

                model_key = f"{target}_{team_type}"
                self.models[model_key].fit(X_train_scaled, y_train)
                y_pred = self.models[model_key].predict(X_test_scaled)

                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                results[model_key] = {'mae': mae, 'r2': r2}

                print(f"MAE: {mae:.3f}, R²: {r2:.3f}")

                self.scalers[model_key] = scaler

        print("\nToate modelele au fost antrenate!")
        return results

    def test_all_models_and_save(self, test_size=0.3, csv_path="all_predictions.csv"):
        """
        Testează toate modelele și salvează rezultatele într-un CSV cu coloanele originale
        și predicțiile corespunzătoare.
        """
        print("Testarea tuturor modelelor...")

        df_results = self.df.copy()

        # Clasificare și regresie principale
        for target_name in ['outcome', 'goals', 'score']:
            print(f"\nTestare model pentru: {target_name}")
            X, y = self.prepare_data(target_name)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            y_pred = self.models[target_name].predict(X_test)

            # Salvează predicțiile în dataframe-ul final
            match_indices = y_test.index
            df_results.loc[match_indices, f"Predicted_{target_name}"] = y_pred

        # Modele statistici LSTM / RandomForest pentru fiecare echipă
        stat_targets = ['corners', 'shots_on_target', 'possession', 'yellow_cards',
                        'fouls', 'tackles', 'passes', 'shots_total', 'xg']

        for target in stat_targets:
            for team_type in ['home', 'away']:
                model_key = f"{target}_{team_type}"
                if model_key not in self.models:
                    continue

                print(f"Testare model pentru: {target} ({team_type})")
                X, y = self.prepare_data(target, team_type)
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42
                )

                scaler = self.scalers[model_key]
                X_test_scaled = scaler.transform(X_test)

                y_pred = self.models[model_key].predict(X_test_scaled)

                # Salvează predicțiile
                match_indices = y_test.index
                df_results.loc[match_indices, f"Predicted_{target}_{team_type}"] = y_pred

        df_results.to_csv(csv_path, index=False)
        print(f"\nToate predicțiile au fost salvate în: {csv_path}")

        return df_results

    def predict_future_match(self, date, time, home_team, away_team):
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            time_obj = datetime.strptime(time, "%H:%M").time()
        except:
            print("Formatul datei sau orei este incorect.")
            return None

        if home_team not in self.team_encoder.classes_ or away_team not in self.team_encoder.classes_:
            print("Una dintre echipe nu există în dataset.")
            return None

        home_stats = self._get_team_stats(home_team)
        away_stats = self._get_team_stats(away_team)

        if not home_stats or not away_stats:
            print("Nu s-au putut obține statisticile pentru echipe.")
            return None

        X_new_home = self._prepare_prediction_features(home_stats, away_stats, home_team, away_team, 'home')
        X_new_away = self._prepare_prediction_features(away_stats, home_stats, away_team, home_team, 'away')

        if X_new_home is None or X_new_away is None:
            return None

        predictions = {'home': {}, 'away': {}}

        pred_outcome = self.models['outcome'].predict(X_new_home)[0]
        proba_outcome = self.models['outcome'].predict_proba(X_new_home)[0]

        pred_goals = self.models['goals'].predict(X_new_home)[0]
        pred_score = self.models['score'].predict(X_new_home)[0]
        stat_targets = ['corners', 'shots_on_target', 'possession', 'yellow_cards',
                        'fouls', 'tackles', 'passes', 'shots_total', 'xg']

        for target in stat_targets:
            home_key = f"{target}_home"
            if home_key in self.models:
                X_scaled = self.scalers[home_key].transform(X_new_home)
                predictions['home'][target] = self.models[home_key].predict(X_scaled)[0]

            away_key = f"{target}_away"
            if away_key in self.models:
                X_scaled = self.scalers[away_key].transform(X_new_away)
                predictions['away'][target] = self.models[away_key].predict(X_scaled)[0]

        self._display_predictions(home_team, away_team, date, time, pred_outcome,
                                  proba_outcome, pred_goals, pred_score, predictions)

        self._save_prediction_to_csv(date, time, home_team, away_team, {
            'outcome': (pred_outcome, proba_outcome),
            'goals': pred_goals,
            'score': pred_score,
            'stats': predictions})

        return {
            'outcome': (pred_outcome, proba_outcome),
            'goals': pred_goals,
            'score': pred_score,
            'stats': predictions}

    def _get_team_stats(self, team_name):
        team_matches = self.df[self.df["Team"] == team_name]
        if team_matches.empty:
            return None

        return team_matches.iloc[-1].to_dict()

    def _prepare_prediction_features(self, team_stats, opponent_stats, team_name, opponent_name, perspective):
        try:
            features = {}

            features['win_rate_global'] = team_stats.get('win_rate_global', 0.5)
            features['win_rate_lastN'] = team_stats.get('win_rate_lastN', 0.5)

            if perspective == 'home':
                features['home_win_rate'] = team_stats.get('home_win_rate', 0.5)
                features['away_win_rate'] = opponent_stats.get('away_win_rate', 0.5)
                features['Home_encoded'] = 1
            else:
                features['home_win_rate'] = opponent_stats.get('home_win_rate', 0.5)
                features['away_win_rate'] = team_stats.get('away_win_rate', 0.5)
                features['Home_encoded'] = 0

            h2h_matches = self.df[
                ((self.df["Team"] == team_name) & (self.df["Opponent"] == opponent_name)) |
                ((self.df["Team"] == opponent_name) & (self.df["Opponent"] == team_name))]
            features['h2h_win_rate'] = h2h_matches['h2h_win_rate'].mean() if not h2h_matches.empty else 0.5
            features['form_score'] = team_stats.get('form_score', 0.5)
            features['goal_diff_win_rate'] = team_stats.get('goal_diff_win_rate', 0)
            features['weighted_outcome'] = team_stats.get('weighted_outcome', 0.5)
            features['team_goals'] = team_stats.get('team_goals', 1)
            features['opponent_goals'] = opponent_stats.get('team_goals', 1)
            features['Rank'] = team_stats.get('Rank', 10)
            features['opponent_rank'] = opponent_stats.get('Rank', 10)

            for stat_feature in self.stat_features:
                if perspective == 'home':
                    features[stat_feature] = team_stats.get(stat_feature, 0)
                else:
                    stat_feature_away = (stat_feature
                                         .replace('_team','_opponent')) \
                        if '_team' in stat_feature else stat_feature.replace('_opponent', '_team')
                    features[stat_feature] = team_stats.get(stat_feature_away, 0)

            X_new = pd.DataFrame([features])

            available_features = [f for f in self.all_features if f in self.df.columns]
            X_new = X_new[available_features]

            return X_new

        except Exception as e:
            print(f"Eroare la prepararea features: {e}")
            return None


        except Exception as e:
            print(f"Eroare la prepararea features: {e}")
            return None

    def _display_predictions(self, home_team, away_team, date, time, pred_outcome,
                             proba_outcome, pred_goals, pred_score, stat_predictions):
        print(f"\n{'=' * 80}")
        print(f"PREDICȚIE MECCI: {home_team} vs {away_team}")
        print(f"Data: {date} Ora: {time}")
        print(f"{'=' * 80}")

        mapping_outcome = {0: "EGAL", 1: f"{home_team} CÂȘTIGĂ", 2: f"{away_team} CÂȘTIGĂ"}
        outcome_text = mapping_outcome.get(pred_outcome, "NECUNOSCUT")

        print(f"\nREZULTAT FINAL PREZIS: {outcome_text}")
        print(f"PROBABILITĂȚI:")
        print(f"{home_team}: {proba_outcome[1]:.1%}")
        print(f"Egal: {proba_outcome[0]:.1%}")
        print(f"{away_team}: {proba_outcome[2]:.1%}")

        # Score prediction
        print(f"\nSCOR PREZIS: {pred_score}")

        mapping_goals = {0: "0", 1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6+"}
        print(f"TOTAL GOLURI PREZIS: {mapping_goals.get(pred_goals, 'NECUNOSCUT')}")

        print(f"\nSTATISTICI PREZISE:")
        print(f"\n{'─' * 40}")
        print(f"{'STATISTICĂ':<20} {'HOME':<10} {'AWAY':<10}")
        print(f"{'─' * 40}")

        stats_display = [
            ('Cornere', 'corners'),
            ('Șuturi pe poartă', 'shots_on_target'),
            ('Posesie (%)', 'possession'),
            ('Cartonașe galbene', 'yellow_cards'),
            ('Faulturi', 'fouls'),
            ('Tackle-uri', 'tackles'),
            ('Pase', 'passes'),
            ('Șuturi total', 'shots_total'),
            ('xG', 'xg')]

        for display_name, stat_key in stats_display:
            home_val = stat_predictions['home'].get(stat_key, 0)
            away_val = stat_predictions['away'].get(stat_key, 0)

            if stat_key == 'possession':
                total = home_val + away_val
                if total > 0:
                    home_val = (home_val / total) * 100
                    away_val = (away_val / total) * 100
                print(f"{display_name:<20} {home_val:.1f}%     {away_val:.1f}%")
            else:
                print(f"{display_name:<20} {home_val:.1f}       {away_val:.1f}")

        print(f"{'─' * 40}")
        print(f"{'=' * 80}")

    def _save_prediction_to_csv(self, date, time, home_team, away_team, predictions, filename="predictions_log.csv"):
        outcome_map = {0: "EGAL", 1: f"{home_team} CÂȘTIGĂ", 2: f"{away_team} CÂȘTIGĂ"}
        pred_outcome, proba_outcome = predictions['outcome']

        row = {
            "Date": date,
            "Time": time,
            "Home_Team": home_team,
            "Away_Team": away_team,
            "Predicted_Outcome": outcome_map.get(pred_outcome, "NECUNOSCUT"),
            "Proba_Home_Win": f"{proba_outcome[1]:.3f}",
            "Proba_Draw": f"{proba_outcome[0]:.3f}",
            "Proba_Away_Win": f"{proba_outcome[2]:.3f}",
            "Predicted_Score": predictions['score'],
            "Predicted_Goals": predictions['goals'],}

        for side in ["home", "away"]:
            for stat, val in predictions["stats"][side].items():
                row[f"{stat}_{side}"] = round(val, 2)

        df_row = pd.DataFrame([row])

        file_exists = os.path.isfile(filename)
        df_row.to_csv(filename, mode="a", header=not file_exists, index=False, encoding="utf-8-sig")
        print(f"Predicția a fost salvată în {filename}")