# player_stats.py - "Top Player Stats Page".
# uses the live api when we have a key, otherwise falls back to the
# sample db so the page isn't just a blank error message.

import plotly.express as px
import streamlit as st

from api_helper import fetch_top_stats, has_key
from db_helper import run_query, db_ready

CRICKET_COLORS = ["#1B5E20", "#C8102E", "#F9A825", "#2E7D32", "#8D6E63", "#546E7A"]

STAT_TYPES = {
    "mostRuns": "Most Runs",
    "mostWickets": "Most Wickets",
    "highestScore": "Highest Score",
    "bestBowling": "Best Bowling Figures",
    "mostSixes": "Most Sixes",
}


def render():
    st.header("📊 Top Player Stats")

    if has_key():
        st.caption("Live leaderboard from the Cricbuzz API.")
        stat_type = st.selectbox("Category", list(STAT_TYPES), format_func=lambda k: STAT_TYPES[k])
        headers, values = fetch_top_stats(stat_type)
        if not values:
            st.info("No data came back for this category.")
            return
        rows = [v.get("values", v) if isinstance(v, dict) else v for v in values]
        st.dataframe(rows, use_container_width=True)
        return

    st.warning(
        "No API key set, so these leaderboards are computed from the sample "
        "database instead of live Cricbuzz data. Add CRICBUZZ_API_KEY to switch "
        "over (see Home page)."
    )

    if not db_ready():
        st.error("Database isn't seeded - run `python generate_data.py` first.")
        return

    tab1, tab2, tab3 = st.tabs(["Most Runs", "Most Wickets", "Best Strike Rate"])

    with tab1:
        fmt = st.selectbox("Format", ["Test", "ODI", "T20I"], key="runs_fmt")
        df = run_query("""
            SELECT p.full_name AS player, p.country,
                   SUM(b.runs_scored) AS total_runs,
                   ROUND(SUM(b.runs_scored) * 1.0 / NULLIF(SUM(b.is_out), 0), 2) AS batting_average
            FROM batting_scorecards b
            JOIN players p ON b.player_id = p.player_id
            WHERE b.format = :fmt
            GROUP BY p.player_id, p.full_name, p.country
            ORDER BY total_runs DESC
            LIMIT 15
        """, {"fmt": fmt})
        st.dataframe(df, use_container_width=True, hide_index=True)
        fig = px.bar(df.sort_values("total_runs"), x="total_runs", y="player", orientation="h",
                     color_discrete_sequence=CRICKET_COLORS, title=f"Top run scorers - {fmt}")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fmt = st.selectbox("Format", ["Test", "ODI", "T20I"], key="wkt_fmt")
        df = run_query("""
            SELECT p.full_name AS player, p.country,
                   SUM(bo.wickets_taken) AS total_wickets,
                   ROUND(SUM(bo.runs_conceded) * 1.0 / NULLIF(SUM(bo.balls_bowled) / 6.0, 0), 2) AS economy_rate
            FROM bowling_scorecards bo
            JOIN players p ON bo.player_id = p.player_id
            WHERE bo.format = :fmt
            GROUP BY p.player_id, p.full_name, p.country
            ORDER BY total_wickets DESC
            LIMIT 15
        """, {"fmt": fmt})
        st.dataframe(df, use_container_width=True, hide_index=True)
        fig = px.bar(df.sort_values("total_wickets"), x="total_wickets", y="player", orientation="h",
                     color_discrete_sequence=CRICKET_COLORS, title=f"Top wicket takers - {fmt}")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        fmt = st.selectbox("Format", ["Test", "ODI", "T20I"], key="sr_fmt")
        df = run_query("""
            SELECT p.full_name AS player, p.country,
                   ROUND(AVG(CASE WHEN b.balls_faced > 0 THEN b.runs_scored * 100.0 / b.balls_faced END), 2) AS strike_rate,
                   SUM(b.runs_scored) AS total_runs
            FROM batting_scorecards b
            JOIN players p ON b.player_id = p.player_id
            WHERE b.format = :fmt
            GROUP BY p.player_id, p.full_name, p.country
            HAVING total_runs >= 300
            ORDER BY strike_rate DESC
            LIMIT 15
        """, {"fmt": fmt})
        st.dataframe(df, use_container_width=True, hide_index=True)
        fig = px.bar(df.sort_values("strike_rate"), x="strike_rate", y="player", orientation="h",
                     color_discrete_sequence=CRICKET_COLORS, title=f"Best strike rate, min 300 runs - {fmt}")
        st.plotly_chart(fig, use_container_width=True)
