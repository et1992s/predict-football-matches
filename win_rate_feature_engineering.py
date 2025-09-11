import pandas as pd
from sklearn.preprocessing import LabelEncoder

class FootballWinRateFeatures:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        self.team_encoder = LabelEncoder()
        if "Goals For" in self.df.columns:
            self.df.rename(columns={"Goals For": "team_goals", "Goals Against": "opponent_goals"}, inplace=True)

    def encode_columns(self):
        all_teams = pd.concat([self.df["Team"], self.df["Opponent"]]).unique()
        self.team_encoder.fit(all_teams)

        self.df["Team_encoded"] = self.team_encoder.transform(self.df["Team"])
        self.df["Opponent_encoded"] = self.team_encoder.transform(self.df["Opponent"])

        self.df["Home_encoded"] = self.df["Home/Away"].map({"home": 1, "away": 0})
        self.df["Outcome_encoded"] = self.df["Outcome"].map({"W": 1, "D": 0, "L": 2})
        self.df["Target_encoded"] = self.df["Target_Winner"].map({"team": 1, "opponent": 2, "draw": 0})
        return self

    def create_winrate_features(self, N_recent: int = 3):
        df = self.df.copy()
        df = df.sort_values(["Team", "Date", "Time"]).reset_index(drop=True)

        df['win_rate_global'] = 0.0
        df['win_rate_lastN'] = 0.0
        df['home_win_rate'] = 0.0
        df['away_win_rate'] = 0.0
        df['h2h_win_rate'] = 0.5
        df['win_streak'] = 0
        df['form_score'] = 0.0
        df['goal_diff'] = df['team_goals'] - df['opponent_goals']
        df['goal_diff_win_rate'] = 0.0
        df['weighted_outcome'] = 0.0

        weights = [0.3,0.2,0.1]

        for team in df['Team'].unique():
            team_mask = df['Team'] == team
            team_df = df[team_mask].copy()
            cum_wins = 0
            streak = 0
            form_window = []

            team_indices = df[team_mask].index.tolist()
            for i, idx in enumerate(team_indices):
                row = df.loc[idx]

                cum_wins += 1 if row['Outcome']=='W' else 0
                games_played = i + 1
                df.at[idx,'win_rate_global'] = cum_wins / games_played

                recent_idx = team_indices[max(0,i-N_recent+1):i+1]
                df.at[idx,'win_rate_lastN'] = (df.loc[recent_idx,'Outcome']=='W').mean()

                home_mask = (df['Team']==team) & (df['Home/Away']=='home') & (df.index<=idx)
                away_mask = (df['Team']==team) & (df['Home/Away']=='away') & (df.index<=idx)
                df.at[idx,'home_win_rate'] = (df.loc[home_mask,'Outcome']=='W').mean() if home_mask.sum()>0 else 0.5
                df.at[idx,'away_win_rate'] = (df.loc[away_mask,'Outcome']=='W').mean() if away_mask.sum()>0 else 0.5

                h2h_mask = (df['Team']==team) & (df['Opponent']==row['Opponent']) & (df.index<idx)
                df.at[idx,'h2h_win_rate'] = (df.loc[h2h_mask,'Outcome']=='W').mean() if h2h_mask.sum()>0 else 0.5

                streak = streak+1 if row['Outcome']=='W' else 0
                df.at[idx,'win_streak'] = streak

                form_window.append(1 if row['Outcome']=='W' else 0)
                form_window = form_window[-len(weights):]
                weighted_form = sum(f*w for f,w in zip(form_window[::-1], weights[-len(form_window):]))
                df.at[idx,'form_score'] = weighted_form

                recent_goal_diff = df.loc[recent_idx,'team_goals'] - df.loc[recent_idx,'opponent_goals']
                df.at[idx,'goal_diff_win_rate'] = (recent_goal_diff>0).mean()

                df.at[idx,'weighted_outcome'] = (0.5*df.at[idx,'win_rate_lastN'] +
                                                 0.3*df.at[idx,'form_score'] +
                                                 0.2*df.at[idx,'goal_diff_win_rate'])

        fill_neutral = ['win_rate_global','win_rate_lastN','home_win_rate','away_win_rate',
                        'h2h_win_rate','form_score','goal_diff_win_rate','weighted_outcome']
        df[fill_neutral] = df[fill_neutral].fillna(0.5)

        self.df = df
        return self

    def save_csv(self, output_path: str):
        self.df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"CSV cu win rate features salvat: {output_path}")
        return self
