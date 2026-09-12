# crud_ops.py - "CRUD Operations Page"
# basic create/read/update/delete forms for players and matches.
# nothing fancy, just enough to demonstrate data management on top of
# the sql database.

import streamlit as st

from db_helper import run_query, run_action, db_ready

ROLES = ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"]
BAT_STYLES = ["Right-hand bat", "Left-hand bat"]
BOWL_STYLES = ["None", "Right-arm fast", "Right-arm fast-medium", "Right-arm medium",
               "Right-arm off break", "Right-arm leg break", "Left-arm fast",
               "Left-arm fast-medium", "Left-arm orthodox", "Left-arm wrist spin"]


def render():
    st.header("⚙️ CRUD Operations")
    st.caption("Add, edit and remove player / match records in the database.")

    if not db_ready():
        st.error("Database isn't seeded yet - run `python generate_data.py` first.")
        return

    tab_players, tab_matches = st.tabs(["Players", "Matches"])

    with tab_players:
        players_tab()

    with tab_matches:
        matches_tab()


def players_tab():
    teams = run_query("SELECT team_id, team_name FROM teams ORDER BY team_name")
    team_map = dict(zip(teams["team_name"], teams["team_id"]))

    action = st.radio("action", ["Create", "Read", "Update", "Delete"], horizontal=True, key="p_action")

    if action == "Create":
        st.subheader("Add player")
        with st.form("new_player", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Full name")
            team = c1.selectbox("Team", list(team_map))
            role = c1.selectbox("Role", ROLES)
            bat_style = c2.selectbox("Batting style", BAT_STYLES)
            bowl_style = c2.selectbox("Bowling style", BOWL_STYLES)
            debut = c2.number_input("Debut year", 1950, 2026, 2020)

            if st.form_submit_button("Add"):
                if not name.strip():
                    st.error("need a name")
                else:
                    run_action(
                        """INSERT INTO players (full_name, country, team_id, playing_role, batting_style, bowling_style, debut_year)
                           VALUES (:n, :c, :t, :r, :bs, :bwl, :d)""",
                        {"n": name.strip(), "c": team, "t": team_map[team], "r": role, "bs": bat_style,
                         "bwl": None if bowl_style == "None" else bowl_style, "d": int(debut)},
                    )
                    st.success(f"added {name}")

    elif action == "Read":
        st.subheader("Browse players")
        c1, c2, c3 = st.columns(3)
        country = c1.selectbox("Country", ["All"] + sorted(team_map))
        role = c2.selectbox("Role", ["All"] + ROLES)
        name_like = c3.text_input("Name contains")

        sql = "SELECT player_id, full_name, country, playing_role, batting_style, bowling_style, debut_year FROM players WHERE 1=1"
        params = {}
        if country != "All":
            sql += " AND country = :c"
            params["c"] = country
        if role != "All":
            sql += " AND playing_role = :r"
            params["r"] = role
        if name_like:
            sql += " AND full_name LIKE :n"
            params["n"] = f"%{name_like}%"
        sql += " ORDER BY full_name"

        df = run_query(sql, params)
        st.caption(f"{len(df)} players")
        st.dataframe(df, use_container_width=True, hide_index=True)

    elif action == "Update":
        st.subheader("Edit a player")
        players = run_query("SELECT player_id, full_name, country FROM players ORDER BY full_name")
        if players.empty:
            st.info("no players yet")
            return
        names = {r.player_id: f"{r.full_name} ({r.country})" for r in players.itertuples()}
        pid = st.selectbox("Player", list(names), format_func=lambda i: names[i])
        cur = run_query("SELECT * FROM players WHERE player_id = :id", {"id": pid}).iloc[0]

        with st.form("edit_player"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Full name", cur["full_name"])
            team = c1.selectbox("Team", list(team_map),
                                 index=list(team_map).index(cur["country"]) if cur["country"] in team_map else 0)
            role = c1.selectbox("Role", ROLES, index=ROLES.index(cur["playing_role"]) if cur["playing_role"] in ROLES else 0)
            bat_style = c2.selectbox("Batting style", BAT_STYLES,
                                      index=BAT_STYLES.index(cur["batting_style"]) if cur["batting_style"] in BAT_STYLES else 0)
            cur_bowl = cur["bowling_style"] or "None"
            bowl_style = c2.selectbox("Bowling style", BOWL_STYLES,
                                       index=BOWL_STYLES.index(cur_bowl) if cur_bowl in BOWL_STYLES else 0)
            debut = c2.number_input("Debut year", 1950, 2026, int(cur["debut_year"] or 2020))

            if st.form_submit_button("Save"):
                run_action(
                    """UPDATE players SET full_name=:n, country=:c, team_id=:t, playing_role=:r,
                       batting_style=:bs, bowling_style=:bwl, debut_year=:d WHERE player_id=:id""",
                    {"n": name.strip(), "c": team, "t": team_map[team], "r": role, "bs": bat_style,
                     "bwl": None if bowl_style == "None" else bowl_style, "d": int(debut), "id": int(pid)},
                )
                st.success("saved")

    elif action == "Delete":
        st.subheader("Remove a player")
        players = run_query("SELECT player_id, full_name, country FROM players ORDER BY full_name")
        if players.empty:
            st.info("no players yet")
            return
        names = {r.player_id: f"{r.full_name} ({r.country})" for r in players.itertuples()}
        pid = st.selectbox("Player", list(names), format_func=lambda i: names[i], key="del_p")
        cascade = st.checkbox("also delete their batting/bowling/fielding rows", value=True)
        sure = st.checkbox(f"yes, delete {names[pid]}")
        if st.button("Delete", disabled=not sure):
            if cascade:
                run_action("DELETE FROM batting_scorecards WHERE player_id=:id", {"id": int(pid)})
                run_action("DELETE FROM bowling_scorecards WHERE player_id=:id", {"id": int(pid)})
                run_action("DELETE FROM fielding_stats WHERE player_id=:id", {"id": int(pid)})
            run_action("DELETE FROM players WHERE player_id=:id", {"id": int(pid)})
            st.success("deleted")


def matches_tab():
    teams = run_query("SELECT team_id, team_name FROM teams ORDER BY team_name")
    team_map = dict(zip(teams["team_name"], teams["team_id"]))
    id_to_team = dict(zip(teams["team_id"], teams["team_name"]))
    venues = run_query("SELECT venue_id, venue_name, city FROM venues ORDER BY venue_name")
    venue_map = {f"{r.venue_name} ({r.city})": r.venue_id for r in venues.itertuples()}
    series = run_query("SELECT series_id, series_name FROM series ORDER BY start_date DESC")
    series_map = dict(zip(series["series_name"], series["series_id"]))

    action = st.radio("action", ["Create", "Read", "Update", "Delete"], horizontal=True, key="m_action")

    if action == "Create":
        st.subheader("Add match")
        with st.form("new_match", clear_on_submit=True):
            c1, c2 = st.columns(2)
            series_name = c1.selectbox("Series", list(series_map))
            fmt = c1.selectbox("Format", ["Test", "ODI", "T20I"])
            team1 = c1.selectbox("Team 1", list(team_map), key="nm_t1")
            team2 = c1.selectbox("Team 2", [t for t in team_map if t != team1], key="nm_t2")
            venue = c1.selectbox("Venue", list(venue_map))

            match_date = c2.date_input("Date")
            toss_winner = c2.selectbox("Toss winner", [team1, team2])
            toss_decision = c2.selectbox("Toss decision", ["bat", "bowl"])
            result = c2.selectbox("Result", [team1, team2, "Draw / no result"])
            vtype = c2.selectbox("Won by", ["runs", "wickets"], disabled=(result == "Draw / no result"))
            margin = c2.number_input("Margin", min_value=0, value=0, disabled=(result == "Draw / no result"))

            if st.form_submit_button("Add"):
                bat_first = toss_winner if toss_decision == "bat" else (team2 if toss_winner == team1 else team1)
                winner_id = None if result == "Draw / no result" else team_map[result]
                run_action(
                    """INSERT INTO matches (series_id, match_desc, match_type, team1_id, team2_id, venue_id,
                       match_date, toss_winner_id, toss_decision, bat_first_team_id, winner_id, victory_margin, victory_type)
                       VALUES (:sid, :desc, :fmt, :t1, :t2, :v, :dt, :tw, :td, :bf, :w, :m, :vt)""",
                    {"sid": series_map[series_name], "desc": f"{team1} vs {team2}, {fmt}", "fmt": fmt,
                     "t1": team_map[team1], "t2": team_map[team2], "v": venue_map[venue], "dt": match_date.isoformat(),
                     "tw": team_map[toss_winner], "td": toss_decision, "bf": team_map[bat_first], "w": winner_id,
                     "m": None if result == "Draw / no result" else int(margin),
                     "vt": None if result == "Draw / no result" else vtype},
                )
                st.success("match added")

    elif action == "Read":
        st.subheader("Browse matches")
        c1, c2 = st.columns(2)
        fmt = c1.selectbox("Format", ["All", "Test", "ODI", "T20I"])
        team = c2.selectbox("Team", ["All"] + sorted(team_map))

        sql = """
            SELECT m.match_id, m.match_desc, m.match_type, t1.team_name AS team1, t2.team_name AS team2,
                   v.venue_name, m.match_date, tw.team_name AS winner, m.victory_margin, m.victory_type
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            JOIN venues v ON m.venue_id = v.venue_id
            LEFT JOIN teams tw ON m.winner_id = tw.team_id
            WHERE 1=1
        """
        params = {}
        if fmt != "All":
            sql += " AND m.match_type = :fmt"
            params["fmt"] = fmt
        if team != "All":
            sql += " AND (t1.team_name = :team OR t2.team_name = :team)"
            params["team"] = team
        sql += " ORDER BY m.match_date DESC LIMIT 200"

        df = run_query(sql, params)
        st.caption(f"{len(df)} matches (most recent 200)")
        st.dataframe(df, use_container_width=True, hide_index=True)

    elif action == "Update":
        st.subheader("Edit a match result")
        matches = run_query("SELECT match_id, match_desc, match_date FROM matches ORDER BY match_date DESC LIMIT 300")
        if matches.empty:
            st.info("no matches yet")
            return
        names = {r.match_id: f"[{r.match_date}] {r.match_desc}" for r in matches.itertuples()}
        mid = st.selectbox("Match", list(names), format_func=lambda i: names[i])
        cur = run_query("SELECT * FROM matches WHERE match_id = :id", {"id": mid}).iloc[0]

        with st.form("edit_match"):
            options = [id_to_team[cur["team1_id"]], id_to_team[cur["team2_id"]], "Draw / no result"]
            cur_result = id_to_team.get(cur["winner_id"], "Draw / no result") if cur["winner_id"] else "Draw / no result"
            result = st.selectbox("Result", options, index=options.index(cur_result))
            vtype = st.selectbox("Won by", ["runs", "wickets"],
                                  index=["runs", "wickets"].index(cur["victory_type"]) if cur["victory_type"] in ["runs", "wickets"] else 0,
                                  disabled=(result == "Draw / no result"))
            margin = st.number_input("Margin", min_value=0, value=int(cur["victory_margin"] or 0),
                                      disabled=(result == "Draw / no result"))

            if st.form_submit_button("Save"):
                winner_id = None if result == "Draw / no result" else team_map[result]
                run_action(
                    "UPDATE matches SET winner_id=:w, victory_margin=:m, victory_type=:vt WHERE match_id=:id",
                    {"w": winner_id, "m": None if result == "Draw / no result" else int(margin),
                     "vt": None if result == "Draw / no result" else vtype, "id": int(mid)},
                )
                st.success("saved")

    elif action == "Delete":
        st.subheader("Remove a match")
        matches = run_query("SELECT match_id, match_desc, match_date FROM matches ORDER BY match_date DESC LIMIT 300")
        if matches.empty:
            st.info("no matches yet")
            return
        names = {r.match_id: f"[{r.match_date}] {r.match_desc}" for r in matches.itertuples()}
        mid = st.selectbox("Match", list(names), format_func=lambda i: names[i], key="del_m")
        cascade = st.checkbox("also delete this match's scorecards", value=True)
        sure = st.checkbox(f"yes, delete: {names[mid]}")
        if st.button("Delete match", disabled=not sure):
            if cascade:
                run_action("DELETE FROM batting_scorecards WHERE match_id=:id", {"id": int(mid)})
                run_action("DELETE FROM bowling_scorecards WHERE match_id=:id", {"id": int(mid)})
                run_action("DELETE FROM fielding_stats WHERE match_id=:id", {"id": int(mid)})
            run_action("DELETE FROM matches WHERE match_id=:id", {"id": int(mid)})
            st.success("deleted")
