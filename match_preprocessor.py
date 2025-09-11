import pandas as pd
import numpy as np

class MatchPreprocessor:
    def __init__(self, csv_file, zero_threshold=0.95):
        self.csv_file = csv_file
        self.df = None
        self.zero_threshold = zero_threshold

    def load_csv(self):
        self.df = pd.read_csv(self.csv_file)
        return self

    def fill_missing(self, value=0):
        self.df.fillna(value, inplace=True)
        return self

    def convert_numeric_and_percentage(self):
        for col in self.df.columns:
            s = self.df[col].astype(str)

            if s.str.contains('%').any():
                self.df[col] = s.str.extract(r'(\d+\.?\d*)')[0].astype(float) / 100
            else:
                self.df[col] = pd.to_numeric(s.str.replace(r'[^0-9.-]', '', regex=True), errors='coerce').fillna(0)
        return self

    def split_goals_column(self):
        if "Goals" in self.df.columns:
            goals = self.df["Goals"].astype(str)
            home_away = goals.apply(lambda x: pd.Series([
                int(x.split(":")[0]) if ":" in x else int(str(int(x))[:2]),
                int(x.split(":")[1]) if ":" in x else int(str(int(x))[2:])]))
            home_away.columns = ["team_total_goals_home", "team_total_goals_away"]
            self.df = pd.concat([self.df.drop(columns=["Goals"]), home_away], axis=1)
            print("'Goals' a fost împărțit în home/away și eliminată coloana originală")
        return self

    def drop_zero_heavy_columns(self):
        zero_fraction = (self.df == 0).mean()
        cols_to_drop = zero_fraction[zero_fraction > self.zero_threshold].index.tolist()
        if cols_to_drop:
            print(f"Eliminăm coloanele cu >{self.zero_threshold*100:.0f}% valori zero: {cols_to_drop}")
            self.df.drop(columns=cols_to_drop, inplace=True)
        return self

    def normalize_large_stats(self, threshold=100):
        for col in self.df.select_dtypes(include=[np.number]).columns:
            if self.df[col].max() > threshold:
                self.df[col] = self.df[col] / (self.df[col].max() + 1e-6)
        return self

    def get_df(self):
        return self.df

    def save_csv(self, output_file):
        self.df.to_csv(output_file, index=False)
        print(f"CSV curățat salvat: '{output_file}'")
        return self
