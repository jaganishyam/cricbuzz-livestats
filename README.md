# 🏏 Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics

A cricket analytics dashboard built with Streamlit, a SQL database (SQLite
by default, Postgres/MySQL supported), and the Cricbuzz Cricket API
(via RapidAPI). Live match data, player leaderboards, 25 SQL practice
queries, and CRUD data management, all in one app with a cricket-pitch
themed UI.

## Pages

- **Home** — status of the DB / API key
- **Live Matches** — live/recent matches from the Cricbuzz API
- **Top Player Stats** — most runs / wickets / strike rate leaderboards
  (live via API, or from the sample DB when there's no key yet)
- **SQL Queries & Analytics** — all 25 practice queries from the brief,
  run live against the database, with a quick auto-chart and CSV export
- **CRUD Operations** — add / edit / delete players and matches

## Project layout

Everything lives at the top level, no nested packages - one file per
concern, wired together from `app.py`:

```
cricbuzz-livestats/
├── app.py              # entry point - sidebar nav + page routing + theme css
├── db_helper.py         # db connection (sqlite/postgres/mysql), run_query / run_action
├── api_helper.py        # cricbuzz api wrapper
├── live_matches.py       # Live Matches page
├── player_stats.py       # Top Player Stats page
├── sql_analytics.py      # SQL Queries & Analytics page
├── crud_ops.py           # CRUD Operations page
├── sql_queries.py        # the 25 queries + question text
├── schema.sql             # table definitions
├── generate_data.py       # builds the sample database
├── check_queries.py       # sanity-checks all 25 queries return rows
├── data/cricbuzz.db        # sqlite file (generated)
├── requirements.txt
├── .env.example
└── .streamlit/
    ├── secrets.toml.example
    └── config.toml
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Build the sample database (needed once, before running the app):

```bash
python generate_data.py
```

This fabricates ~450 matches (2019-2026, Test/ODI/T20I) across 12 teams
with full batting/bowling/fielding scorecards, because the live Cricbuzz
API doesn't expose the years of historical data the 25 SQL questions
need. Check it worked with:

```bash
python check_queries.py
```

Run the app:

```bash
streamlit run app.py
```

## Adding a live Cricbuzz API key (optional)

Live Matches and Top Player Stats use the
[Cricbuzz Cricket API on RapidAPI](https://rapidapi.com/cricketapilive/api/cricbuzz-cricket/)
(free tier available). Once you have a key, either:

- copy `.env.example` to `.env` and set `CRICBUZZ_API_KEY`, or
- copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and
  set it under `[api]` (this is also the format Streamlit Community
  Cloud's Secrets settings expects)

Without a key those two pages fall back to a "no key yet" message /
sample-database leaderboard. SQL Analytics and CRUD work fully either way.

## Switching to PostgreSQL or MySQL

All db access goes through `db_helper.py`, so this is config only:

```
DB_ENGINE=postgresql   # or mysql
DB_HOST=localhost
DB_PORT=5432           # 3306 for mysql
DB_NAME=cricbuzz
DB_USER=your_user
DB_PASSWORD=your_password
```

Install the driver you need (`psycopg2-binary` for Postgres, `pymysql`
for MySQL), point at an empty database, then run `generate_data.py`
again - it builds the schema and loads the sample data there instead.

## Notes on the sample data

- It's synthetic, generated to give every SQL query something meaningful
  to return - not real player stats. Swap in real data any time through
  the CRUD page or by pointing `db_helper.py` at a database you've
  populated another way.
- Partnership runs (Q13, Q24) are approximated as the combined scores of
  two adjacent batting positions in the same innings, since there's no
  ball-by-ball log.
- "Last 30 days" / "last 3 years" (Q2, Q22) are measured from the newest
  match date in the dataset, not today's real date - this is a fixed
  snapshot, not a live feed.
- CRUD deletes offer a "cascade" checkbox for related scorecard rows,
  since SQLite doesn't enforce foreign keys by default.

## Tech stack

Python, Streamlit, SQL (SQLite / PostgreSQL / MySQL), SQLAlchemy,
Cricbuzz REST API (RapidAPI), pandas, requests, Plotly
