# live_matches.py - the "Live Match Page" from the brief.
# pulls whatever's currently live/recent from the cricbuzz api.

import streamlit as st
from api_helper import fetch_live_matches, has_key


def render():
    st.header("🔴 Live Matches")
    st.caption("Live and recently completed matches straight from Cricbuzz.")

    if not has_key():
        st.warning(
            "No API key configured yet, so there's nothing to fetch. Once you add "
            "CRICBUZZ_API_KEY (see the Home page), this page will show a card per "
            "match with the teams, venue, status and current score, plus a refresh "
            "button to re-poll (cached 60s to be nice to the free API tier)."
        )
        return

    if st.button("🔄 Refresh"):
        fetch_live_matches.clear()

    with st.spinner("pulling live scores..."):
        matches = fetch_live_matches()

    if not matches:
        st.info("Nothing live right now.")
        return

    categories = sorted(set(m["category"] for m in matches if m["category"]))
    pick = st.selectbox("Category", ["All"] + categories)
    shown = matches if pick == "All" else [m for m in matches if m["category"] == pick]

    st.caption(f"{len(shown)} of {len(matches)} matches")

    for m in shown:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{m['team1']} vs {m['team2']}**")
            c1.caption(f"{m['series']} — {m['desc']}")
            c2.markdown(f"`{m['state']}`")

            place = ", ".join(x for x in [m["ground"], m["city"]] if x)
            if place:
                st.caption(f"📍 {place}")
            if m["status"]:
                st.write(m["status"])

            score = m.get("score") or {}
            if score:
                cols = st.columns(len(score))
                for i, (team, s) in enumerate(score.items()):
                    innings = s.get("inngs1", {}) if isinstance(s, dict) else {}
                    if innings:
                        cols[i].metric(team, f"{innings.get('runs','-')}/{innings.get('wickets','-')}",
                                        f"{innings.get('overs','-')} ov")
