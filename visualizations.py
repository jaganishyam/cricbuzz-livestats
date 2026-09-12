# visualizations.py - "Visualizations" page.
# a handful of presentation-ready charts over the sample database - kpis
# up top, then team/player/format breakdowns. doesn't touch the live api
# at all, so it always has something to show regardless of whether a
# cricbuzz key is configured.

import plotly.express as px
import streamlit as st

from db_helper import run_query, db_ready

# single-hue per chart (magnitude, not identity) so each ranking reads as
# "one metric, sorted" rather than a rainbow of unrelated bars. the format
# donut is the only chart with more than one series in it, so that's the
# only place a real categorical set is needed.
RUNS_HUE = "#22C55E"      # app's brand green
WICKETS_HUE = "#F5B301"   # gold, matches the CRUD accent used elsewhere
SIXES_HUE = "#3987E5"
TREND_HUE = "#22C55E"
FORMAT_COLORS = ["#3987E5", "#D95926", "#199E70"]  # Test / ODI / T20I

CHART_TEMPLATE = "plotly_dark"


def _style(fig, height=380):
    fig.update_layout(
        template=CHART_TEMPLATE,
        paper_bgcolor="#141A23",
        plot_bgcolor="#141A23",
        font_color="#E5E7EB",
        margin=dict(l=10, r=10, t=40, b=10),
        height=height,
    )
    return fig


def render():
    st.header("📈 Visualizations")
    st.caption("Team, player and format breakdowns from the sample database - built for a quick presentation view.")

    if not db_ready():
        st.error("Database isn't seeded yet.")
        st.code("python generate_data.py", language="bash")
        return

    totals = run_query("SELECT COUNT(*) AS n FROM matches")
    players = run_query("SELECT COUNT(*) AS n FROM players")
    runs = run_query("SELECT SUM(runs_scored) AS n FROM batting_scorecards")
    wkts = run_query("SELECT SUM(wickets_taken) AS n FROM bowling_scorecards")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Matches", f"{int(totals['n'][0]):,}")
    c2.metric("Players", f"{int(players['n'][0]):,}")
    c3.metric("Runs Scored", f"{int(runs['n'][0]):,}")
    c4.metric("Wickets Taken", f"{int(wkts['n'][0]):,}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Runs by team")
        df = run_query("""
            SELECT t.team_name AS team, SUM(b.runs_scored) AS total_runs
            FROM batting_scorecards b
            JOIN teams t ON b.team_id = t.team_id
            GROUP BY t.team_id, t.team_name
            ORDER BY total_runs DESC
            LIMIT 8
        """)
        fig = px.bar(df.sort_values("total_runs"), x="total_runs", y="team", orientation="h",
                     color_discrete_sequence=[RUNS_HUE],
                     labels={"total_runs": "Runs", "team": ""})
        st.plotly_chart(_style(fig), use_container_width=True)

    with col2:
        st.subheader("Wickets by team")
        df = run_query("""
            SELECT t.team_name AS team, SUM(bo.wickets_taken) AS total_wickets
            FROM bowling_scorecards bo
            JOIN teams t ON bo.team_id = t.team_id
            GROUP BY t.team_id, t.team_name
            ORDER BY total_wickets DESC
            LIMIT 8
        """)
        fig = px.bar(df.sort_values("total_wickets"), x="total_wickets", y="team", orientation="h",
                     color_discrete_sequence=[WICKETS_HUE],
                     labels={"total_wickets": "Wickets", "team": ""})
        st.plotly_chart(_style(fig), use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Matches by format")
        df = run_query("""
            SELECT match_type AS format, COUNT(*) AS matches
            FROM matches
            GROUP BY match_type
            ORDER BY matches DESC
        """)
        fig = px.pie(df, names="format", values="matches", hole=0.45,
                     color_discrete_sequence=FORMAT_COLORS)
        fig.update_traces(textinfo="label+percent")
        st.plotly_chart(_style(fig), use_container_width=True)

    with col4:
        st.subheader("Top 10 six-hitters")
        df = run_query("""
            SELECT p.full_name AS player, SUM(b.sixes) AS sixes
            FROM batting_scorecards b
            JOIN players p ON b.player_id = p.player_id
            GROUP BY p.player_id, p.full_name
            ORDER BY sixes DESC
            LIMIT 10
        """)
        fig = px.bar(df.sort_values("sixes"), x="sixes", y="player", orientation="h",
                     color_discrete_sequence=[SIXES_HUE],
                     labels={"sixes": "Sixes", "player": ""})
        st.plotly_chart(_style(fig), use_container_width=True)

    st.subheader("Runs scored by year")
    df = run_query("""
        SELECT strftime('%Y', m.match_date) AS year, SUM(b.runs_scored) AS total_runs
        FROM batting_scorecards b
        JOIN matches m ON b.match_id = m.match_id
        GROUP BY year
        ORDER BY year
    """)
    fig = px.line(df, x="year", y="total_runs", markers=True,
                  color_discrete_sequence=[TREND_HUE],
                  labels={"year": "", "total_runs": "Runs"})
    st.plotly_chart(_style(fig, height=320), use_container_width=True)
