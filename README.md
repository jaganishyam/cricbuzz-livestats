# 🏏 Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics

**Live app:** [cricbuzz-livestats-shyamjagani.streamlit.app](https://cricbuzz-livestats-shyamjagani.streamlit.app/)

A cricket analytics dashboard that brings three things into one screen: live match
scores and player leaderboards pulled from a real cricket data feed, a SQL database
built to answer 25 real cricket questions, and a set of presentation-ready charts —
plus a screen to manage the underlying data. Built with Python, Streamlit, SQL, and
Plotly.

## About the project

I built this while moving my career into data analytics, as a project that shows
range rather than one narrow skill: pulling in data from a live external API,
designing and querying a proper relational database, visualizing the results, and
handling the create/read/update/delete side of the data too. Cricket was the subject
because it's a domain almost anyone already understands, which meant I could spend
my effort on the data and analytics rather than explaining the sport.

## Pages

| Page | What it does |
|---|---|
| 🏠 **Home** | Project overview plus a quick health check — is the database ready, is the live feed reachable |
| 🔴 **Live Matches** | Matches happening right now or recently finished, pulled live from the Cricbuzz API — teams, venue, score, result |
| 📊 **Top Player Stats** | Live leaderboards — most runs, most wickets, most sixes, highest scores |
| 🧮 **SQL Queries & Analytics** | All 25 practice questions from the project brief, run live against the database, each with its result table, a quick auto-chart, and CSV export |
| 📈 **Visualizations** | Headline KPIs and presentation-style charts — runs and wickets by team, matches by format, top six-hitters, and a year-by-year scoring trend |
| ⚙️ **CRUD Operations** | Add, edit, and delete players and matches, with cascading delete for related scorecard rows |

## Where the data comes from

These two sources are independent — the app doesn't merge them:

- **Live data:** Live Matches and Top Player Stats are powered by the
  [Cricbuzz Cricket API](https://rapidapi.com/cricketapilive/api/cricbuzz-cricket/)
  (via RapidAPI), in real time whenever the feed is available.
- **My own generated database:** every database-driven page — SQL Queries &
  Analytics, Visualizations, and CRUD Operations — runs entirely on a synthetic
  dataset I built myself: roughly 450 matches (2019–2026, across Test, ODI, and
  T20I) and 240 players, complete with full batting, bowling, and fielding
  scorecards, rivalries, and home-ground advantage baked in. The live feed can't
  supply the years of historical depth the 25 SQL questions need, so this dataset
  gives the analytics side something real to work with regardless of API
  availability.

A few honesty notes on the sample data: partnership-run questions approximate a
partnership as the combined score of two adjacent batting positions (there's no
ball-by-ball log), and "last 30 days" / "last 3 years" style questions are measured
from the newest match date in the dataset rather than today's real date, since it's
a fixed snapshot rather than a live feed.

## The 25 SQL questions

Written across three difficulty levels, from simple lookups to genuinely advanced
analytical queries:

**Beginner (8)**
1. Find all players who represent India, with role, batting style, and bowling style
2. Matches played in the last 30 days, sorted most recent first
3. Top 10 highest run scorers in ODI cricket
4. Venues with a seating capacity over 50,000
5. Total match wins per team, most wins first
6. Player count by playing role (Batsman, Bowler, All-rounder, Wicket-keeper)
7. Highest individual batting score in each format (Test, ODI, T20I)
8. Cricket series that started in 2024

**Intermediate (8)**

9. All-rounders with 1000+ runs and 50+ wickets in their career
10. Details of the last 20 completed matches
11. Player performance compared across formats, for those who've played 2+ formats
12. Team performance at home vs. away
13. Batting partnerships of adjacent positions scoring 100+ combined
14. Bowling economy and workload by venue, for bowlers with 3+ matches there
15. Player performance in close matches (decided by <50 runs or <5 wickets)
16. Year-over-year batting trend since 2020, for players with 5+ matches in a year

**Advanced (9)**

17. Whether winning the toss correlates with winning the match, by toss decision
18. Most economical limited-overs bowlers, minimum 10 matches
19. Most consistent batsmen by standard deviation of runs, since 2022
20. Matches played and batting average by format, for players with 20+ total matches
21. A weighted performance ranking combining batting, bowling, and fielding
22. Head-to-head prediction analysis between teams with 5+ meetings in 3 years
23. Recent player form and momentum from their last 10 innings
24. Best-performing batting partnerships, for pairs with 5+ partnerships together
25. Quarterly time-series of a player's career phase — ascending, declining, or stable

Every query runs as real SQL under the hood, but each one was written to answer
something a cricket fan would actually wonder about, not to show off syntax.

## Tech stack

Python · Streamlit · SQL (SQLite by default, swappable to PostgreSQL/MySQL) ·
SQLAlchemy · Cricbuzz Cricket API (RapidAPI) · pandas · Plotly

## Project layout

Everything lives at the top level — one file per concern, wired together from
`app.py` — rather than a nested package structure:

```
cricbuzz-livestats/
├── app.py              # entry point - sidebar nav, page routing, theme css
├── db_helper.py        # db connection (sqlite/postgres/mysql), run_query / run_action
├── api_helper.py       # Cricbuzz API wrapper
├── live_matches.py     # Live Matches page
├── player_stats.py     # Top Player Stats page
├── sql_analytics.py    # SQL Queries & Analytics page
├── visualizations.py   # Visualizations page
├── crud_ops.py         # CRUD Operations page
├── sql_queries.py      # the 25 queries + question text
├── schema.sql          # table definitions
├── generate_data.py    # builds the sample database
├── check_queries.py    # sanity-checks all 25 queries return rows
├── data/cricbuzz.db     # sqlite database (generated)
├── requirements.txt
└── .streamlit/config.toml
```

## Author

**Shyam Jagani**
[LinkedIn](https://linkedin.com/in/shyam-jagani-356535141) ·
[GitHub](https://github.com/jaganishyam)
