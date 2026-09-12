# api_helper.py
# small wrapper around the Cricbuzz Cricket API on RapidAPI.
# get a key here: https://rapidapi.com/cricketapilive/api/cricbuzz-cricket/
# put it in .env as CRICBUZZ_API_KEY or in .streamlit/secrets.toml under [api]

import os
import requests
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_HOST = "cricbuzz-cricket.p.rapidapi.com"
BASE = "https://" + API_HOST


def get_api_key():
    try:
        if "api" in st.secrets and st.secrets["api"].get("CRICBUZZ_API_KEY"):
            return st.secrets["api"]["CRICBUZZ_API_KEY"]
    except Exception:
        pass
    return os.getenv("CRICBUZZ_API_KEY")


def has_key():
    return bool(get_api_key())


def _headers():
    return {"X-RapidAPI-Key": get_api_key() or "", "X-RapidAPI-Host": API_HOST}


def _call(endpoint, params=None):
    if not has_key():
        return None
    try:
        r = requests.get(BASE + endpoint, headers=_headers(), params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as err:
        st.warning(f"Cricbuzz API call failed: {err}")
        return None


@st.cache_data(ttl=60, show_spinner=False)
def fetch_live_matches():
    data = _call("/matches/v1/live")
    if not data:
        return []

    matches = []
    for block in data.get("typeMatches", []):
        category = block.get("matchType", "")
        for sm in block.get("seriesMatches", []):
            wrapper = sm.get("seriesAdWrapper", {})
            series_name = wrapper.get("seriesName", "")
            for m in wrapper.get("matches", []):
                info = m.get("matchInfo", {})
                matches.append({
                    "category": category,
                    "series": series_name,
                    "desc": info.get("matchDesc", ""),
                    "team1": info.get("team1", {}).get("teamName", ""),
                    "team2": info.get("team2", {}).get("teamName", ""),
                    "status": info.get("status", ""),
                    "state": info.get("state", ""),
                    "ground": info.get("venueInfo", {}).get("ground", ""),
                    "city": info.get("venueInfo", {}).get("city", ""),
                    "score": m.get("matchScore", {}),
                })
    return matches


@st.cache_data(ttl=300, show_spinner=False)
def fetch_top_stats(stat_type="mostRuns"):
    data = _call("/stats/v1/topstats/0", params={"statsType": stat_type})
    if not data:
        return [], []
    return data.get("headers", []), data.get("values", [])
