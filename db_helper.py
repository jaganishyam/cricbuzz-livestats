# db_helper.py
# handles the database connection for the whole app.
# using sqlalchemy instead of plain sqlite3 so the same code also works
# with postgres/mysql later if i ever move off sqlite (the project brief
# asked for db-agnostic design so keeping this centralised here).

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "cricbuzz.db"


def _setting(key, fallback=None):
    # secrets.toml takes priority over .env / os env vars
    try:
        if "database" in st.secrets and key in st.secrets["database"]:
            return st.secrets["database"][key]
    except Exception:
        pass
    return os.getenv(key, fallback)


def _make_url():
    engine_name = (_setting("DB_ENGINE", "sqlite") or "sqlite").lower()

    if engine_name == "sqlite":
        path = Path(_setting("DB_PATH", str(DEFAULT_DB_PATH)))
        path.parent.mkdir(parents=True, exist_ok=True)
        return "sqlite:///" + str(path), {"check_same_thread": False}

    if engine_name == "postgresql":
        port = _setting("DB_PORT") or "5432"
        url = "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
            _setting("DB_USER", ""), _setting("DB_PASSWORD", ""),
            _setting("DB_HOST", "localhost"), port, _setting("DB_NAME", "cricbuzz"),
        )
        return url, {}

    if engine_name == "mysql":
        port = _setting("DB_PORT") or "3306"
        url = "mysql+pymysql://{}:{}@{}:{}/{}".format(
            _setting("DB_USER", ""), _setting("DB_PASSWORD", ""),
            _setting("DB_HOST", "localhost"), port, _setting("DB_NAME", "cricbuzz"),
        )
        return url, {}

    raise ValueError("DB_ENGINE must be sqlite, postgresql or mysql, got: " + engine_name)


@st.cache_resource(show_spinner=False)
def get_engine():
    url, connect_args = _make_url()
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


def run_query(sql, params=None):
    # for SELECTs - returns a dataframe
    eng = get_engine()
    with eng.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def run_action(sql, params=None):
    # for INSERT / UPDATE / DELETE, commits automatically
    eng = get_engine()
    with eng.begin() as conn:
        result = conn.execute(text(sql), params or {})
        return result.rowcount


def db_ready():
    # quick check used on the home page to see if generate_data.py has run yet
    try:
        out = run_query("SELECT COUNT(*) AS n FROM players")
        return out.iloc[0]["n"] > 0
    except Exception:
        return False


def current_engine_name():
    return (_setting("DB_ENGINE", "sqlite") or "sqlite").lower()
