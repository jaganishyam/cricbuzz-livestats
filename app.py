# app.py
# entry point for the cricbuzz livestats app. everything is wired up
# through a sidebar menu here instead of streamlit's auto multipage
# folder, mostly because it's easier to control what shows up in the
# nav and it's how i've seen most of these dashboards done.
#
# run with: streamlit run app.py

import streamlit as st

from db_helper import db_ready, current_engine_name
from api_helper import has_key
import live_matches
import player_stats
import sql_analytics
import crud_ops

st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")

# ---- cricket-themed styling -------------------------------------------
# keeping this pretty simple - green for the pitch/outfield feel in the
# sidebar, cricket-ball red for buttons/accents, cream background for
# the main area (like an old scorebook page).
st.markdown("""
<style>
    .stApp {
        background-color: #FAF9F4;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1B5E20 0%, #2E7D32 55%, #1B5E20 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #F1F8E9 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.25);
    }
    div.stButton > button, div.stFormSubmitButton > button {
        background-color: #C8102E;
        color: white;
        border: none;
        border-radius: 6px;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        background-color: #A50D25;
        color: white;
    }
    .stadium-banner {
        background: linear-gradient(90deg, #1B5E20, #2E7D32);
        padding: 18px 24px;
        border-radius: 10px;
        border-left: 6px solid #C8102E;
        margin-bottom: 18px;
    }
    .stadium-banner h1 {
        color: white;
        margin: 0;
        font-size: 1.9rem;
    }
    .stadium-banner p {
        color: #E8F5E9;
        margin: 4px 0 0 0;
    }
    div[data-testid="stMetric"] {
        background-color: #E8F5E9;
        border: 1px solid #C8E6C9;
        border-radius: 8px;
        padding: 10px 14px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="stadium-banner">
<h1>🏏 Cricbuzz LiveStats</h1>
<p>Real-Time Cricket Insights &amp; SQL-Based Analytics</p>
</div>
""", unsafe_allow_html=True)

PAGES = {
    "Home": None,
    "Live Matches": live_matches,
    "Top Player Stats": player_stats,
    "SQL Queries & Analytics": sql_analytics,
    "CRUD Operations": crud_ops,
}

with st.sidebar:
    st.markdown("### 🏏 Navigation")
    choice = st.radio("go to", list(PAGES.keys()), label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Status**")
    st.write("DB:", "✅ ready" if db_ready() else "❌ not seeded")
    st.write("Engine:", current_engine_name())
    st.write("API key:", "✅ set" if has_key() else "❌ not set")

if choice == "Home":
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("What's in here")
        st.markdown("""
        | Page | What it does |
        |---|---|
        | 🔴 Live Matches | Live/recent matches from the Cricbuzz API |
        | 📊 Top Player Stats | Run/wicket leaderboards |
        | 🧮 SQL Queries & Analytics | The 25 practice queries from the brief, run live against the db |
        | ⚙️ CRUD Operations | Add / edit / delete players and matches |
        """)
        st.subheader("Stack")
        st.write("Python, Streamlit, SQL (SQLite/Postgres/MySQL), Cricbuzz REST API, pandas, SQLAlchemy, Plotly")

    with col2:
        st.subheader("Status")
        if db_ready():
            st.success("Database is seeded and ready to query.")
        else:
            st.error("Database not seeded yet.")
            st.code("python generate_data.py", language="bash")

        if has_key():
            st.success("Cricbuzz API key found.")
        else:
            st.warning("No Cricbuzz API key set yet.")
            st.caption(
                "Live Matches & Top Player Stats need a free key from "
                "[RapidAPI's Cricbuzz Cricket API](https://rapidapi.com/cricketapilive/api/cricbuzz-cricket/). "
                "Drop it in `.env` as CRICBUZZ_API_KEY, or in `.streamlit/secrets.toml`. "
                "Everything else works fine without it."
            )

    st.info("Use the sidebar to jump between pages.")

elif choice == "Live Matches":
    live_matches.render()

elif choice == "Top Player Stats":
    player_stats.render()

elif choice == "SQL Queries & Analytics":
    sql_analytics.render()

elif choice == "CRUD Operations":
    crud_ops.render()
