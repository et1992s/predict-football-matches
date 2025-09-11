import numpy as np
import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import altair as alt
from match_predictor import FootballMatchPredictor
from main import scrape_and_save_standings, scrape_and_save_matches, scrape_and_save_fixtures, StandingsProcessor, \
    MatchPreprocessor, FootballWinRateFeatures

# --- Config Streamlit ---
st.set_page_config(page_title="Football Predictor MVP", layout="wide")

# --- CSS culori fotbal reci ---
st.markdown("""
    <style>
    /* === METRICS (Predicted Future Match) === */
    div[data-testid="stMetricValue"] {
        color: #E6DFB2 !important;  /* auriu în loc de verde */
        font-weight: bold !important;
        font-size: 22px !important;
    }

    div[data-testid="stMetric"] {
        background: rgba(30, 60, 114, 0.7) !important; /* fundal albastru translucid */
        border: 2px solid #E6DFB2 !important;          /* chenar auriu */
        border-radius: 12px !important;
        padding: 12px !important;
        color: #E0F7FA !important;
    }
    
    /* Background general */
    .stApp { 
        background: linear-gradient(to bottom right, #1E3C72, #2A5298); /* albastru închis spre albastru deschis */
        color: #E0F7FA; /* text alb-verzui deschis */
    }

    /* Carduri / containere */
    .css-1d391kg { 
        background-color: #8BB28B;  /* verde închis pentru carduri */
        color: #E0F7FA;
        border-radius: 12px;
        padding: 10px;
    }

    /* Selectbox și inputuri */
    .stSelectbox, .stButton {
        background-color: #2A52AA; /* albastru deschis */
        color: #E0F7FA;
    }

    /* Headings */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #A8D5BA; /* verde deschis */
    }

    /* Dataframe table headers */
    .stDataFrame th {
        background-color: #1E3C72; /* albastru închis */
        color: #E0F7FA;
    }

    /* Dataframe table cells */
    .stDataFrame td {
        background-color: #8BB28B; /* verde închis */
        color: #E0F7FA;
    }
    </style>
""", unsafe_allow_html=True)

# --- Liga și sezoane ---
leagues = {
    "romania_superliga": {
        "name": "Romania Superliga 2024-2025",
        "standings_url": "https://www.flashscore.com/football/romania/superliga-2024-2025/standings/#/QkBSrPPD/standings/overall/",
        "results_url": "https://www.flashscore.com/football/romania/superliga-2024-2025/results/"
    },
    "romania_superliga_2025_2026": {
        "name": "Romania Superliga 2025-2026",
        "standings_url": "https://www.flashscore.com/football/romania/superliga/standings/#/02YI7tIj/standings/overall/",
        "results_url": "https://www.flashscore.com/football/romania/superliga/results/",
        "fixtures_url": "https://www.flashscore.com/football/romania/superliga/fixtures/"
    },
    "la_liga": {
        "name": "La Liga 2024-2025",
        "standings_url": "https://www.flashscore.com/football/spain/laliga-2024-2025/standings/#/dINOZk9Q/standings/overall/",
        "results_url": "https://www.flashscore.com/football/spain/laliga-2024-2025/results/",
    },
    "la_liga_2025_2026": {
        "name": "La Liga 2025-2026",
        "standings_url": "https://www.flashscore.com/football/spain/laliga/standings/#/vcm2MhGk/",
        "results_url": "https://www.flashscore.com/football/spain/laliga/results/",
        "fixtures_url": "https://www.flashscore.com/football/spain/laliga/fixtures/"
    }
}

# --- Sezon curent selectat implicit ---
selected_league = st.selectbox("Select League/Season", list(leagues.keys()), index=1)
league_info = leagues[selected_league]
st.title(f"{league_info['name']}")

# --- Paths ---
standings_file_json = f"processed/standings_{selected_league}.json"
matches_file_json = f"processed/all_matches_{selected_league}.json"
fixtures_file_json = f"processed/fixtures_{selected_league}.json"
winrate_file_csv = f"processed/standings_with_winrate_features_{selected_league}.csv"

# --- Download data if not exists ---
if not os.path.exists(standings_file_json):
    st.info("Downloading standings...")
    scrape_and_save_standings(league_info["standings_url"], standings_file_json)

if not os.path.exists(matches_file_json):
    st.info("Downloading results...")
    scrape_and_save_matches(league_info["results_url"], matches_file_json)

if "fixtures_url" in league_info and not os.path.exists(fixtures_file_json):
    st.info("Downloading fixtures...")
    scrape_and_save_fixtures(league_info["fixtures_url"], fixtures_file_json)

# --- Procesare și creare fișier winrate ---
if not os.path.exists(winrate_file_csv):
    st.info("Processing data and creating winrate features...")
    processor = StandingsProcessor(standings_file_json, matches_file_json)
    processor.flatten_to_long().clean_eda()
    cleaned_csv = f"processed/standings_with_matches_{selected_league}_clean.csv"
    processor.save_csv(cleaned_csv)

    preprocessor = MatchPreprocessor(cleaned_csv)
    preprocessor.load_csv() \
        .fill_missing(0) \
        .convert_numeric_and_percentage() \
        .split_goals_column() \
        .drop_zero_heavy_columns() \
        .normalize_large_stats() \
        .save_csv(f"processed/standings_with_matches_{selected_league}_cleaned.csv")
    preprocessed_csv = f"processed/standings_with_matches_{selected_league}_clean.csv"

    ff = FootballWinRateFeatures(preprocessed_csv)
    ff.encode_columns().create_winrate_features(N_recent=10).save_csv(winrate_file_csv)

# --- Load standings ---
df_standings = pd.DataFrame()
if os.path.exists(standings_file_json):
    with open(standings_file_json, "r", encoding="utf-8") as f:
        standings_data = json.load(f)
    df_standings = pd.json_normalize(standings_data["standings"])
    st.subheader("🏆 Standings")
    st.dataframe(df_standings)

# --- Load results ---
df_results = pd.DataFrame()
if os.path.exists(matches_file_json):
    with open(matches_file_json, "r", encoding="utf-8") as f:
        matches_data = json.load(f)
    df_results = pd.json_normalize(matches_data["matches"])
    if not df_results.empty:
        st.subheader("📊 Results")
        display_cols = ["date", "home", "away", "home_goals", "away_goals", "status"]
        st.dataframe(df_results[display_cols])

# --- Load fixtures ---
df_fixtures = pd.DataFrame()
if os.path.exists(fixtures_file_json):
    with open(fixtures_file_json, "r", encoding="utf-8") as f:
        fixtures_data = json.load(f)
    df_fixtures = pd.json_normalize(fixtures_data["matches"])

# --- Combine future matches ---
future_matches = pd.DataFrame()
if not df_results.empty:
    future_results = df_results[df_results["status"] == "NOT STARTED"]
    future_matches = pd.concat([future_results, df_fixtures], ignore_index=True)
elif not df_fixtures.empty:
    future_matches = df_fixtures

# --- Predict Future Match doar pentru sezonul curent 2025-2026 ---
if "2025_2026" in selected_league:
    st.subheader("⚽ Predict Future Match")
    if not future_matches.empty:
        future_matches["match_str"] = future_matches.apply(
            lambda x: f"{x['home']} vs {x['away']} on {x['date']} {x.get('time', '')}", axis=1
        )

        # Drop-down cu stil integrat
        selected_match = st.selectbox(
            "Select a match",
            future_matches["match_str"],
            key="match_select"
        )

        # CSS pentru dropdown și buton
        st.markdown("""
            <style>
            /* === FUNDAL GENERAL === */
            .stApp { 
                background: linear-gradient(to bottom right, #1E3C72, #2A5298); 
                color: #E0F7FA; 
            }

            /* === CARDURI / CONTAINERE === */
            .css-1d391kg { 
                background-color: #0B3D0B;  
                color: #E0F7FA;
                border-radius: 12px;
                padding: 10px;
            }

            /* === HEADINGS === */
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
                color: #A8D5BA; 
            }

            /* === TABELE === */
            .stDataFrame th {
                background-color: #1E3C72; 
                color: #E0F7FA;
            }
            .stDataFrame td {
                background-color: #0B3D0B; 
                color: #E0F7FA;
            }

            /* === SELECTBOX === */
            div.stSelectbox {
                background: transparent !important;    /* eliminăm pătratul deschis */
                box-shadow: none !important;
            }

            /* Label-ul ("Select League/Season", "Select a match") */
            div.stSelectbox label {
                background: transparent !important;
                color: #E0F7FA !important;
                margin-bottom: 6px !important;  /* spațiu între label și câmp */
                font-weight: bold !important;
            }

            /* Container dropdown */
            div.stSelectbox > div {
                width: auto !important;       
                min-width: 340px;             
                max-width: 500px;             
                margin: 0;
                background: transparent !important;
            }

            /* Zona vizibilă cu text selectat */
            div[data-baseweb="select"] > div {
                background: rgba(30, 60, 114, 0.65) !important;
                border: 1px solid #2A5298 !important;
                border-radius: 10px !important;
                padding: 12px 16px !important;   /* mai mult spațiu sus-jos */
                min-height: 50px !important;     /* suficient să nu taie textul */
                display: flex;
                align-items: center;             /* text centrat pe verticală */
                color: #E0F7FA !important;
                font-size: 16px !important;
                line-height: 1.6em !important;
            }

            /* Dropdown-ul de opțiuni */
            div[data-baseweb="select"] ul {
                background: rgba(30, 60, 114, 0.95) !important;
                color: #E0F7FA !important;
            }

            /* Hover pe opțiuni */
            div[data-baseweb="select"] li:hover {
                background: #2A5298 !important;
                color: #FFFFFF !important;
            }

            /* === BUTON (Predict) === */
            div.stButton {
                background: transparent !important;   /* eliminăm fundalul gri */
                box-shadow: none !important;
            }

            div.stButton > button {
                background: linear-gradient(to bottom right, #1E3C72, #2A5298) !important;
                color: #E0F7FA !important;
                border: 1px solid #2A5298 !important;
                border-radius: 10px !important;
                padding: 10px 20px !important;
                font-size: 16px !important;
                font-weight: bold !important;
            }

            div.stButton > button:hover {
                background: linear-gradient(to bottom right, #2A5298, #1E3C72) !important;
                color: #FFFFFF !important;
                border: 1px solid #FFFFFF !important;
            }
            </style>
        """, unsafe_allow_html=True)

        if st.button("Predict"):
            predictor = FootballMatchPredictor([winrate_file_csv])
            predictor.train_models()

            home_team, away_team = selected_match.split(" vs ")[0], selected_match.split(" vs ")[1].split(" on ")[0]

            date_time_str = selected_match.split(" on ")[1].strip()
            parts = date_time_str.split()
            date_obj = datetime.strptime(parts[0], "%d.%m.%Y")
            date_formatted = date_obj.strftime("%Y-%m-%d")
            time_part = parts[1] if len(parts) > 1 else "00:00"

            predictions = predictor.predict_future_match(
                date=date_formatted,
                time=time_part,
                home_team=home_team,
                away_team=away_team
            )

            st.markdown(f"### Predictions: {home_team} vs {away_team} ({date_time_str})")
            if predictions:
                # --- Columns scor ---
                col1, col2 = st.columns(2)

                metric_bg_color = "linear-gradient(to bottom right, #B2C4E2, #A0B0C0)"  # albastru-gri deschis
                metric_text_color = "#FFFFFF"  # alb

                col1.markdown(f"""
                    <div style="
                        background: {metric_bg_color};
                        color: {metric_text_color};
                        border-radius: 12px;
                        padding: 16px;
                        text-align: center;
                        font-size: 16px;
                        font-weight: bold;">
                        {home_team}<br>{predictions['score'].split(':')[0]}
                    </div>
                """, unsafe_allow_html=True)

                col2.markdown(f"""
                    <div style="
                        background: {metric_bg_color};
                        color: {metric_text_color};
                        border-radius: 12px;
                        padding: 16px;
                        text-align: center;
                        font-size: 16px;
                        font-weight: bold;">
                        {away_team}<br>{predictions['score'].split(':')[1]}
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"**Total Goals:** {predictions['goals']}")

                outcome_idx, probs = predictions["outcome"]
                prob_df = pd.DataFrame({
                    "Team": [home_team, "Draw", away_team],
                    "Probability (%)": [probs[1] * 100, probs[0] * 100, probs[2] * 100]
                })

                # Parametri gradient
                n_steps = 100  # număr de segmente pe bară
                colors = alt.Scale(
                    domain=[0, n_steps - 1],
                    range=['#FFFFCC', '#FFFF99', '#FFB266', '#FF9933', '#FF6600', '#FF0000']  # galben -> roșu
                )

                # Creăm DataFrame pentru fiecare segment
                gradient_df = pd.DataFrame()
                for i, row in prob_df.iterrows():
                    steps = np.linspace(0, row['Probability (%)'] / 100, n_steps)
                    temp = pd.DataFrame({
                        'Team': row['Team'],
                        'Step': np.arange(n_steps),
                        'Height': steps
                    })
                    gradient_df = pd.concat([gradient_df, temp], ignore_index=True)

                # Chart cu gradient real
                chart = alt.Chart(gradient_df).mark_bar(size=50).encode(
                    x=alt.X('Team', sort=[home_team, 'Draw', away_team]),
                    y=alt.Y('Height', scale=alt.Scale(domain=[0, 1])),
                    color=alt.Color('Step', scale=colors, legend=None)
                ).properties(
                    width=50,
                    height=600
                )

                st.altair_chart(chart, use_container_width=True)

                # --- Stats table ---
                stats = predictions["stats"]
                df_stats = pd.DataFrame(stats).T.rename(index={"home": home_team, "away": away_team})
                st.subheader("📈 Predicted Match Stats")
                st.dataframe(df_stats.style.format("{:.2f}").highlight_max(axis=1, color="#B2C4E2"))
            else:
                st.write("Predictions could not be generated for this match.")
    else:
        st.write("Nu există meciuri viitoare pentru sezonul selectat.")

# --- Display fixtures ---
if not df_fixtures.empty:
    st.subheader("📅 Upcoming Fixtures")
    display_cols = ["date", "home", "away", "time", "status"]
    df_display_fixtures = df_fixtures.copy()
    for col in display_cols:
        if col not in df_display_fixtures.columns:
            df_display_fixtures[col] = ""
    st.dataframe(df_display_fixtures[display_cols])
