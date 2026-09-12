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
 
# ---- theme -------------------------------------------------------------
# dark dashboard look now instead of the bright green pitch version -
# dark navy/charcoal base (set in .streamlit/config.toml, base="dark"),
# with flat dark cards, a green/gold/red cricket accent trio, and pill
# style nav + tabs. kept the CSS scoped to specific elements rather than
# any `*` wildcard - a blanket selector broke streamlit's icon font last
# time (the sidebar collapse arrow rendered as literal text), so anything
# that touches font-family or color here targets a named element only.
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    html, body { font-family: 'Inter', sans-serif; }
 
    .stApp { background-color: #0B0F14; }
 
    /* ---- sidebar ---- */
    section[data-testid="stSidebar"] {
        background-color: #10151D;
        border-right: 1px solid #212836;
    }
    section[data-testid="stSidebar"] h3 {
        color: #E5E7EB;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    section[data-testid="stSidebar"] hr { border-color: #212836; }
 
    /* nav items as flat pill rows, active one picked out in green */
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background: #141A23;
        border: 1px solid #212836;
        border-radius: 8px;
        padding: 9px 12px;
        margin-bottom: 6px;
        width: 100%;
        transition: border-color 0.12s ease-in-out, background 0.12s ease-in-out;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        border-color: #22C55E;
        background: #182018;
    }
 
    /* ---- top project banner: flat dark card, not a loud gradient ---- */
    .project-banner {
        background: #141A23;
        border: 1px solid #212836;
        border-left: 4px solid #22C55E;
        border-radius: 12px;
        padding: 20px 26px;
        margin-bottom: 20px;
    }
    .project-banner h1 {
        color: #F3F4F6;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .project-banner p {
        color: #9CA3AF;
        margin: 6px 0 0 0;
        font-size: 1rem;
    }
 
    /* ---- headings ---- */
    h1, h2, h3, h4 { color: #F3F4F6; font-weight: 700; }
    p, li, span, label { color: #C9CDD3; }
 
    /* ---- buttons: flat pill, green primary accent ---- */
    div.stButton > button, div.stFormSubmitButton > button, div.stDownloadButton > button {
        background: #22C55E;
        color: #0B0F14;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5em 1.2em;
        transition: background 0.12s ease-in-out;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover, div.stDownloadButton > button:hover {
        background: #16A34A;
        color: #0B0F14;
    }
 
    /* ---- metric tiles: uppercase micro-label + big bold number ---- */
    div[data-testid="stMetric"] {
        background: #141A23;
        border: 1px solid #212836;
        border-left: 3px solid #22C55E;
        border-radius: 10px;
        padding: 14px 18px;
    }
    div[data-testid="stMetricLabel"] {
        text-transform: uppercase;
        letter-spacing: 0.6px;
        font-size: 0.75rem;
        color: #9CA3AF !important;
    }
 
    /* ---- tabs: green underline on the active tab, like a lot of
       modern dashboards do it ---- */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid #212836; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; color: #9CA3AF; }
    .stTabs [aria-selected="true"] {
        color: #22C55E !important;
        border-bottom: 3px solid #22C55E !important;
    }
 
    /* ---- cards for dataframes / expanders / containers ---- */
    div[data-testid="stDataFrame"] {
        border: 1px solid #212836;
        border-radius: 10px;
        overflow: hidden;
    }
    div[data-testid="stExpander"] {
        background: #141A23;
        border: 1px solid #212836;
        border-radius: 10px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #212836 !important;
        background: #141A23;
    }
 
    /* ---- alert boxes a touch more muted to match the dark card look ---- */
    div[data-testid="stAlert"] { border-radius: 10px; }
 
    /* ---- a little "chip" used on the home page feature row ---- */
    .feature-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #141A23;
        border: 1px solid #212836;
        border-radius: 20px;
        padding: 6px 14px;
        margin: 0 8px 8px 0;
        font-size: 0.88rem;
        color: #C9CDD3;
    }
    .dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; }
</style>
""", unsafe_allow_html=True)
 
st.markdown("""
<div class="project-banner">
<h1>🏏 Cricbuzz LiveStats</h1>
<p>Real-Time Cricket Insights &amp; SQL-Based Analytics</p>
</div>
""", unsafe_allow_html=True)
 
PAGES = {
    "🏠 Home": None,
    "🔴 Live Matches": live_matches,
    "📊 Top Player Stats": player_stats,
    "🧮 SQL Queries & Analytics": sql_analytics,
    "⚙️ CRUD Operations": crud_ops,
}
 
with st.sidebar:
    st.markdown("### Navigation")
    choice = st.radio("go to", list(PAGES.keys()), label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Status**")
    st.write("DB:", "✅ ready" if db_ready() else "❌ not seeded")
    st.write("Engine:", current_engine_name())
    st.write("API key:", "✅ set" if has_key() else "❌ not set")
 
if choice == "🏠 Home":
    st.subheader("About this project")
    st.markdown(
        "Cricbuzz LiveStats pulls together three things that usually live in separate "
        "toy projects - a **live sports API**, a **SQL database with real query practice**, "
        "and **CRUD data entry** - into one dashboard. Live matches and player leaderboards "
        "come straight from the Cricbuzz API; the analytics side runs 25 SQL questions "
        "(beginner through advanced - joins, subqueries, window functions, CTEs) against a "
        "generated database of ~450 matches so there's always real data to query, even without "
        "an API key; and the CRUD page demonstrates basic data management on top of it all."
    )
 
    st.markdown(
        '<span class="feature-chip"><span class="dot" style="background:#EF4444"></span>Live scores via REST API</span>'
        '<span class="feature-chip"><span class="dot" style="background:#22C55E"></span>25 SQL practice queries</span>'
        '<span class="feature-chip"><span class="dot" style="background:#F5B301"></span>Full CRUD on players/matches</span>'
        '<span class="feature-chip"><span class="dot" style="background:#38BDF8"></span>SQLite / Postgres / MySQL</span>',
        unsafe_allow_html=True,
    )
 
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
 
elif choice == "🔴 Live Matches":
    live_matches.render()
 
elif choice == "📊 Top Player Stats":
    player_stats.render()
 
elif choice == "🧮 SQL Queries & Analytics":
    sql_analytics.render()
 
elif choice == "⚙️ CRUD Operations":
    crud_ops.render()
