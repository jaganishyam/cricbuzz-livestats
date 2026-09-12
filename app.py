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
# went a bit further with this pass - proper stadium font, a mowed-pitch
# stripe texture behind everything, a glowing scoreboard banner, pill
# style nav, gradient buttons with a hover lift, card-ish metrics/tabs.
# still just CSS injected once here, nothing fancier than that.
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    /* NOTE: deliberately not forcing font-family on a broad [class*="css"]
       or sidebar `*` selector - streamlit renders its icons (the sidebar
       collapse arrow etc) as ligature text in an icon font, and a blanket
       font override turns those into literal readable text like
       "keyboard_double_arrow_left" instead of the little arrow glyph.
       so the custom font below only touches headings, which are safe. */
    .stApp {
        background-color: #F6F5EE;
        background-image:
            repeating-linear-gradient(115deg, rgba(27,94,32,0.035) 0px, rgba(27,94,32,0.035) 40px, transparent 40px, transparent 80px);
    }

    /* ---- sidebar: pitch gradient + subtle mow stripes ---- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(160deg, #0F3D14 0%, #1B5E20 45%, #2E7D32 75%, #1B5E20 100%);
        background-size: 100% 100%;
        box-shadow: 3px 0 18px rgba(0,0,0,0.18);
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: #F1F8E9;
    }
    /* the collapse-arrow icon has to keep its own icon font, or it renders
       as literal text instead of the little arrow glyph - leave it alone */
    section[data-testid="stSidebarCollapsedControl"] * ,
    button[kind="header"] * {
        font-family: unset !important;
    }
    section[data-testid="stSidebar"] h3 {
        font-family: 'Oswald', sans-serif;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        font-size: 1.05rem;
        border-bottom: 2px solid rgba(200,16,46,0.6);
        padding-bottom: 8px;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.2);
    }
    /* nav radio -> pill style rows */
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 8px;
        padding: 9px 12px;
        margin-bottom: 6px;
        transition: all 0.15s ease-in-out;
        width: 100%;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(255,255,255,0.14);
        border-color: rgba(200,16,46,0.7);
    }

    /* ---- headings ---- */
    h1, h2, h3 {
        font-family: 'Oswald', sans-serif;
        letter-spacing: 0.3px;
    }

    /* ---- buttons: cricket-ball red, gradient + lift on hover ---- */
    div.stButton > button, div.stFormSubmitButton > button, div.stDownloadButton > button {
        background: linear-gradient(135deg, #E4173E 0%, #A50D25 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5em 1.2em;
        box-shadow: 0 3px 8px rgba(165,13,37,0.35);
        transition: transform 0.12s ease-in-out, box-shadow 0.12s ease-in-out;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover, div.stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(165,13,37,0.45);
        color: white;
    }

    /* ---- the top banner ---- */
    .stadium-banner {
        background: linear-gradient(120deg, #0F3D14 0%, #1B5E20 45%, #2E7D32 100%);
        padding: 22px 28px;
        border-radius: 14px;
        border-left: 7px solid #E4173E;
        box-shadow: 0 8px 24px rgba(15,61,20,0.35);
        margin-bottom: 22px;
        position: relative;
        overflow: hidden;
    }
    .stadium-banner::after {
        content: "";
        position: absolute;
        top: -60%; right: -10%;
        width: 260px; height: 260px;
        background: radial-gradient(circle, rgba(255,255,255,0.10) 0%, transparent 70%);
    }
    .stadium-banner h1 {
        color: white;
        margin: 0;
        font-size: 2.1rem;
        font-weight: 700;
    }
    .stadium-banner .ball {
        display: inline-block;
        animation: spin 9s linear infinite;
    }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .stadium-banner p {
        color: #E8F5E9;
        margin: 6px 0 0 0;
        font-size: 1.02rem;
    }

    /* ---- metrics as little scorecards ---- */
    div[data-testid="stMetric"] {
        background: linear-gradient(160deg, #E8F5E9 0%, #DCEEDD 100%);
        border: 1px solid #C8E6C9;
        border-left: 4px solid #2E7D32;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }

    /* ---- tabs with a red underline on the active one ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        color: #A50D25 !important;
        border-bottom: 3px solid #E4173E !important;
    }

    /* ---- dataframes get a card feel ---- */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }

    /* ---- inputs: soft green focus ring instead of default blue ---- */
    div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input {
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="stadium-banner">
<h1><span class="ball">🏏</span> Cricbuzz LiveStats</h1>
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
