# sql_queries.py
# the 25 sql questions from the project brief, all written for sqlite.
# each one is a dict with the question text + the actual query so the
# analytics page can just loop over this list for the dropdown.
#
# couple of notes on the queries below:
#  - partnership runs (q13, q24) = sum of two adjacent batting positions'
#    scores in the same innings. there's no ball by ball partnership table
#    so this is the closest approximation without one.
#  - "last 30 days" / "last 3 years" (q2, q22) are relative to the newest
#    match_date actually in the table, not today's real date, since this
#    is a generated dataset and not a live feed.

QUERIES = [
    {
        "id": 1, "level": "Beginner",
        "title": "Players representing India",
        "question": "Find all players who represent India. Display their full name, playing role, batting style, and bowling style.",
        "sql": """
            SELECT full_name, playing_role, batting_style, bowling_style
            FROM players
            WHERE country = 'India'
            ORDER BY full_name;
        """,
    },
    {
        "id": 2, "level": "Beginner",
        "title": "Matches in the last 30 days",
        "question": "Show all cricket matches that were played in the last 30 days. Include the match description, both team names, venue name with city, and the match date. Sort by most recent matches first.",
        "note": "measured from the latest match_date in this dataset, not the real calendar date",
        "sql": """
            WITH bounds AS (SELECT MAX(match_date) AS max_date FROM matches)
            SELECT m.match_desc,
                   t1.team_name AS team1,
                   t2.team_name AS team2,
                   v.venue_name || ', ' || v.city AS venue,
                   m.match_date
            FROM matches m, bounds
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            JOIN venues v ON m.venue_id = v.venue_id
            WHERE m.match_date >= date(bounds.max_date, '-30 day')
            ORDER BY m.match_date DESC;
        """,
    },
    {
        "id": 3, "level": "Beginner",
        "title": "Top 10 ODI run scorers",
        "question": "List the top 10 highest run scorers in ODI cricket. Show player name, total runs scored, batting average, and number of centuries. Display the highest run scorer first.",
        "sql": """
            SELECT p.full_name,
                   SUM(b.runs_scored) AS total_runs,
                   ROUND(SUM(b.runs_scored) * 1.0 / NULLIF(SUM(b.is_out), 0), 2) AS batting_average,
                   SUM(CASE WHEN b.runs_scored >= 100 THEN 1 ELSE 0 END) AS centuries
            FROM batting_scorecards b
            JOIN players p ON b.player_id = p.player_id
            WHERE b.format = 'ODI'
            GROUP BY p.player_id, p.full_name
            ORDER BY total_runs DESC
            LIMIT 10;
        """,
    },
    {
        "id": 4, "level": "Beginner",
        "title": "Venues with capacity over 50,000",
        "question": "Display all cricket venues that have a seating capacity of more than 50,000 spectators. Show venue name, city, country, and capacity. Order by largest capacity first.",
        "sql": """
            SELECT venue_name, city, country, capacity
            FROM venues
            WHERE capacity > 50000
            ORDER BY capacity DESC;
        """,
    },
    {
        "id": 5, "level": "Beginner",
        "title": "Total wins per team",
        "question": "Calculate how many matches each team has won. Show team name and total number of wins. Display teams with most wins first.",
        "sql": """
            SELECT t.team_name, COUNT(*) AS total_wins
            FROM matches m
            JOIN teams t ON m.winner_id = t.team_id
            GROUP BY t.team_id, t.team_name
            ORDER BY total_wins DESC;
        """,
    },
    {
        "id": 6, "level": "Beginner",
        "title": "Players per playing role",
        "question": "Count how many players belong to each playing role (like Batsman, Bowler, All-rounder, Wicket-keeper). Show the role and count of players for each role.",
        "sql": """
            SELECT playing_role, COUNT(*) AS player_count
            FROM players
            GROUP BY playing_role
            ORDER BY player_count DESC;
        """,
    },
    {
        "id": 7, "level": "Beginner",
        "title": "Highest individual score by format",
        "question": "Find the highest individual batting score achieved in each cricket format (Test, ODI, T20I). Display the format and the highest score for that format.",
        "sql": """
            WITH ranked AS (
                SELECT b.format, b.runs_scored, p.full_name,
                       ROW_NUMBER() OVER (PARTITION BY b.format ORDER BY b.runs_scored DESC) AS rn
                FROM batting_scorecards b
                JOIN players p ON b.player_id = p.player_id
            )
            SELECT format, runs_scored AS highest_score, full_name AS scored_by
            FROM ranked
            WHERE rn = 1
            ORDER BY highest_score DESC;
        """,
    },
    {
        "id": 8, "level": "Beginner",
        "title": "Series started in 2024",
        "question": "Show all cricket series that started in the year 2024. Include series name, host country, match type, start date, and total number of matches planned.",
        "sql": """
            SELECT series_name, host_country, match_type, start_date, total_matches
            FROM series
            WHERE strftime('%Y', start_date) = '2024'
            ORDER BY start_date;
        """,
    },
    {
        "id": 9, "level": "Intermediate",
        "title": "All-rounders with 1000+ runs and 50+ wickets",
        "question": "Find all-rounder players who have scored more than 1000 runs AND taken more than 50 wickets in their career. Display player name, total runs, total wickets, and the cricket format.",
        "sql": """
            WITH batting AS (
                SELECT player_id, format, SUM(runs_scored) AS total_runs
                FROM batting_scorecards GROUP BY player_id, format
            ),
            bowling AS (
                SELECT player_id, format, SUM(wickets_taken) AS total_wickets
                FROM bowling_scorecards GROUP BY player_id, format
            )
            SELECT p.full_name, bat.format, bat.total_runs, bowl.total_wickets
            FROM players p
            JOIN batting bat ON p.player_id = bat.player_id
            JOIN bowling bowl ON p.player_id = bowl.player_id AND bat.format = bowl.format
            WHERE bat.total_runs > 1000 AND bowl.total_wickets > 50
            ORDER BY bat.total_runs DESC;
        """,
    },
    {
        "id": 10, "level": "Intermediate",
        "title": "Last 20 completed matches",
        "question": "Get details of the last 20 completed matches. Show match description, both team names, winning team, victory margin, victory type (runs/wickets), and venue name. Display most recent matches first.",
        "sql": """
            SELECT m.match_desc, t1.team_name AS team1, t2.team_name AS team2,
                   tw.team_name AS winning_team, m.victory_margin, m.victory_type,
                   v.venue_name, m.match_date
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            LEFT JOIN teams tw ON m.winner_id = tw.team_id
            JOIN venues v ON m.venue_id = v.venue_id
            WHERE m.winner_id IS NOT NULL
            ORDER BY m.match_date DESC
            LIMIT 20;
        """,
    },
    {
        "id": 11, "level": "Intermediate",
        "title": "Cross-format performance comparison",
        "question": "Compare each player's performance across different cricket formats. For players who have played at least 2 different formats, show their total runs in Test cricket, ODI cricket, and T20I cricket, along with their overall batting average across all formats.",
        "sql": """
            WITH per_format AS (
                SELECT player_id, format, SUM(runs_scored) AS runs, SUM(is_out) AS outs
                FROM batting_scorecards GROUP BY player_id, format
            ),
            qualified AS (
                SELECT player_id FROM per_format GROUP BY player_id HAVING COUNT(DISTINCT format) >= 2
            )
            SELECT p.full_name,
                   SUM(CASE WHEN pf.format = 'Test' THEN pf.runs ELSE 0 END) AS test_runs,
                   SUM(CASE WHEN pf.format = 'ODI' THEN pf.runs ELSE 0 END) AS odi_runs,
                   SUM(CASE WHEN pf.format = 'T20I' THEN pf.runs ELSE 0 END) AS t20i_runs,
                   ROUND(SUM(pf.runs) * 1.0 / NULLIF(SUM(pf.outs), 0), 2) AS overall_batting_average
            FROM per_format pf
            JOIN players p ON p.player_id = pf.player_id
            WHERE pf.player_id IN (SELECT player_id FROM qualified)
            GROUP BY p.player_id, p.full_name
            ORDER BY overall_batting_average DESC;
        """,
    },
    {
        "id": 12, "level": "Intermediate",
        "title": "Home vs away performance",
        "question": "Analyze each international team's performance when playing at home versus playing away. Determine whether each team played at home or away based on whether the venue country matches the team's country. Count wins for each team in both home and away conditions.",
        "sql": """
            WITH match_teams AS (
                SELECT m.match_id, m.winner_id, v.country AS venue_country,
                       t.team_id, t.team_name, t.country AS team_country
                FROM matches m
                JOIN venues v ON m.venue_id = v.venue_id
                JOIN teams t ON t.team_id = m.team1_id OR t.team_id = m.team2_id
            )
            SELECT team_name,
                   SUM(CASE WHEN team_country = venue_country THEN 1 ELSE 0 END) AS home_matches,
                   SUM(CASE WHEN team_country = venue_country AND winner_id = team_id THEN 1 ELSE 0 END) AS home_wins,
                   SUM(CASE WHEN team_country <> venue_country THEN 1 ELSE 0 END) AS away_matches,
                   SUM(CASE WHEN team_country <> venue_country AND winner_id = team_id THEN 1 ELSE 0 END) AS away_wins
            FROM match_teams
            GROUP BY team_id, team_name
            ORDER BY (home_wins + away_wins) DESC;
        """,
    },
    {
        "id": 13, "level": "Intermediate",
        "title": "100+ run batting partnerships",
        "question": "Identify batting partnerships where two consecutive batsmen (batting positions next to each other) scored a combined total of 100 or more runs in the same innings. Show both player names, their combined partnership runs, and which innings it occurred in.",
        "note": "partnership runs = combined score of two adjacent batting positions (no ball-by-ball log stored)",
        "sql": """
            WITH pos AS (
                SELECT b.match_id, b.team_id, b.format, b.batting_position, b.player_id,
                       b.runs_scored, p.full_name
                FROM batting_scorecards b
                JOIN players p ON b.player_id = p.player_id
            )
            SELECT a.full_name AS batsman_1, c.full_name AS batsman_2,
                   (a.runs_scored + c.runs_scored) AS partnership_runs,
                   m.match_desc AS innings
            FROM pos a
            JOIN pos c ON a.match_id = c.match_id AND a.team_id = c.team_id
                       AND a.format = c.format AND c.batting_position = a.batting_position + 1
            JOIN matches m ON m.match_id = a.match_id
            WHERE (a.runs_scored + c.runs_scored) >= 100
            ORDER BY partnership_runs DESC
            LIMIT 200;
        """,
    },
    {
        "id": 14, "level": "Intermediate",
        "title": "Bowling performance by venue",
        "question": "Examine bowling performance at different venues. For bowlers who have played at least 3 matches at the same venue, calculate their average economy rate, total wickets taken, and number of matches played at each venue. Focus on bowlers who bowled at least 4 overs in each match.",
        "sql": """
            WITH venue_bowling AS (
                SELECT bo.player_id, m.venue_id, bo.match_id,
                       bo.balls_bowled, bo.runs_conceded, bo.wickets_taken
                FROM bowling_scorecards bo
                JOIN matches m ON bo.match_id = m.match_id
                WHERE bo.balls_bowled >= 24
            )
            SELECT p.full_name, v.venue_name,
                   COUNT(DISTINCT vb.match_id) AS matches_played,
                   ROUND(SUM(vb.runs_conceded) * 1.0 / NULLIF(SUM(vb.balls_bowled) / 6.0, 0), 2) AS avg_economy_rate,
                   SUM(vb.wickets_taken) AS total_wickets
            FROM venue_bowling vb
            JOIN players p ON vb.player_id = p.player_id
            JOIN venues v ON vb.venue_id = v.venue_id
            GROUP BY vb.player_id, vb.venue_id
            HAVING COUNT(DISTINCT vb.match_id) >= 3
            ORDER BY total_wickets DESC;
        """,
    },
    {
        "id": 15, "level": "Intermediate",
        "title": "Performance in close matches",
        "question": "Identify players who perform exceptionally well in close matches. A close match is defined as one decided by less than 50 runs OR less than 5 wickets. For these close matches, calculate each player's average runs scored, total close matches played, and how many of those close matches their team won when they batted.",
        "sql": """
            WITH close_matches AS (
                SELECT match_id, winner_id FROM matches
                WHERE (victory_type = 'runs' AND victory_margin < 50)
                   OR (victory_type = 'wickets' AND victory_margin < 5)
            ),
            player_close AS (
                SELECT b.player_id, b.match_id, b.team_id, b.runs_scored, cm.winner_id
                FROM batting_scorecards b
                JOIN close_matches cm ON b.match_id = cm.match_id
            )
            SELECT p.full_name,
                   ROUND(AVG(pc.runs_scored), 2) AS avg_runs_in_close_matches,
                   COUNT(DISTINCT pc.match_id) AS close_matches_played,
                   SUM(CASE WHEN pc.team_id = pc.winner_id THEN 1 ELSE 0 END) AS close_matches_won
            FROM player_close pc
            JOIN players p ON p.player_id = pc.player_id
            GROUP BY p.player_id, p.full_name
            ORDER BY avg_runs_in_close_matches DESC
            LIMIT 100;
        """,
    },
    {
        "id": 16, "level": "Intermediate",
        "title": "Yearly batting trend since 2020",
        "question": "Track how players' batting performance changes over different years. For matches since 2020, show each player's average runs per match and average strike rate for each year. Only include players who played at least 5 matches in that year.",
        "sql": """
            WITH yearly AS (
                SELECT b.player_id, strftime('%Y', m.match_date) AS year,
                       COUNT(DISTINCT b.match_id) AS matches_played,
                       AVG(b.runs_scored) AS avg_runs,
                       AVG(CASE WHEN b.balls_faced > 0 THEN b.runs_scored * 100.0 / b.balls_faced END) AS avg_strike_rate
                FROM batting_scorecards b
                JOIN matches m ON b.match_id = m.match_id
                WHERE m.match_date >= '2020-01-01'
                GROUP BY b.player_id, year
            )
            SELECT p.full_name, y.year, y.matches_played,
                   ROUND(y.avg_runs, 2) AS avg_runs_per_match,
                   ROUND(y.avg_strike_rate, 2) AS avg_strike_rate
            FROM yearly y
            JOIN players p ON p.player_id = y.player_id
            WHERE y.matches_played >= 5
            ORDER BY p.full_name, y.year;
        """,
    },
    {
        "id": 17, "level": "Advanced",
        "title": "Toss advantage analysis",
        "question": "Investigate whether winning the toss gives teams an advantage in winning matches. Calculate what percentage of matches are won by the team that wins the toss, broken down by their toss decision (choosing to bat first or bowl first).",
        "sql": """
            SELECT toss_decision,
                   COUNT(*) AS total_matches,
                   SUM(CASE WHEN toss_winner_id = winner_id THEN 1 ELSE 0 END) AS toss_winner_also_won,
                   ROUND(SUM(CASE WHEN toss_winner_id = winner_id THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS toss_winner_win_pct
            FROM matches
            WHERE winner_id IS NOT NULL AND toss_decision IS NOT NULL
            GROUP BY toss_decision;
        """,
    },
    {
        "id": 18, "level": "Advanced",
        "title": "Most economical limited-overs bowlers",
        "question": "Find the most economical bowlers in limited-overs cricket (ODI and T20 formats). Calculate each bowler's overall economy rate and total wickets taken. Only consider bowlers who have bowled in at least 10 matches and bowled at least 2 overs per match on average.",
        "sql": """
            WITH agg AS (
                SELECT bo.player_id,
                       COUNT(DISTINCT bo.match_id) AS matches_played,
                       SUM(bo.runs_conceded) AS total_runs_conceded,
                       SUM(bo.balls_bowled) AS total_balls,
                       SUM(bo.wickets_taken) AS total_wickets
                FROM bowling_scorecards bo
                JOIN matches m ON bo.match_id = m.match_id
                WHERE m.match_type IN ('ODI', 'T20I')
                GROUP BY bo.player_id
            )
            SELECT p.full_name,
                   ROUND(total_runs_conceded * 1.0 / (total_balls / 6.0), 2) AS economy_rate,
                   total_wickets, matches_played
            FROM agg a
            JOIN players p ON p.player_id = a.player_id
            WHERE matches_played >= 10 AND (total_balls * 1.0 / matches_played) >= 12
            ORDER BY economy_rate ASC
            LIMIT 25;
        """,
    },
    {
        "id": 19, "level": "Advanced",
        "title": "Most consistent batsmen (since 2022)",
        "question": "Determine which batsmen are most consistent in their scoring. Calculate the average runs scored and the standard deviation of runs for each player. Only include players who have faced at least 10 balls per innings and played since 2022. A lower standard deviation indicates more consistent performance.",
        "sql": """
            WITH inns AS (
                SELECT b.player_id, b.runs_scored, b.balls_faced
                FROM batting_scorecards b
                JOIN matches m ON b.match_id = m.match_id
                WHERE m.match_date >= '2022-01-01'
            ),
            qualified AS (
                SELECT player_id FROM inns GROUP BY player_id
                HAVING AVG(balls_faced) >= 10 AND COUNT(*) >= 8
            )
            SELECT p.full_name,
                   ROUND(AVG(i.runs_scored), 2) AS avg_runs,
                   ROUND(SQRT(AVG(i.runs_scored * i.runs_scored) - AVG(i.runs_scored) * AVG(i.runs_scored)), 2) AS stddev_runs
            FROM inns i
            JOIN players p ON p.player_id = i.player_id
            WHERE i.player_id IN (SELECT player_id FROM qualified)
            GROUP BY i.player_id, p.full_name
            ORDER BY stddev_runs ASC
            LIMIT 30;
        """,
    },
    {
        "id": 20, "level": "Advanced",
        "title": "Format-wise match counts and averages",
        "question": "Analyze how many matches each player has played in different cricket formats and their batting average in each format. Show the count of Test matches, ODI matches, and T20 matches for each player, along with their respective batting averages. Only include players who have played at least 20 total matches across all formats.",
        "sql": """
            WITH per_format AS (
                SELECT b.player_id, b.format,
                       COUNT(DISTINCT b.match_id) AS matches,
                       SUM(b.runs_scored) * 1.0 / NULLIF(SUM(b.is_out), 0) AS batting_avg
                FROM batting_scorecards b
                GROUP BY b.player_id, b.format
            ),
            totals AS (
                SELECT player_id, SUM(matches) AS total_matches FROM per_format GROUP BY player_id
            )
            SELECT p.full_name,
                   SUM(CASE WHEN pf.format = 'Test' THEN pf.matches ELSE 0 END) AS test_matches,
                   ROUND(MAX(CASE WHEN pf.format = 'Test' THEN pf.batting_avg END), 2) AS test_avg,
                   SUM(CASE WHEN pf.format = 'ODI' THEN pf.matches ELSE 0 END) AS odi_matches,
                   ROUND(MAX(CASE WHEN pf.format = 'ODI' THEN pf.batting_avg END), 2) AS odi_avg,
                   SUM(CASE WHEN pf.format = 'T20I' THEN pf.matches ELSE 0 END) AS t20i_matches,
                   ROUND(MAX(CASE WHEN pf.format = 'T20I' THEN pf.batting_avg END), 2) AS t20i_avg,
                   MAX(t.total_matches) AS total_matches
            FROM per_format pf
            JOIN players p ON p.player_id = pf.player_id
            JOIN totals t ON t.player_id = pf.player_id
            GROUP BY p.player_id, p.full_name
            HAVING MAX(t.total_matches) >= 20
            ORDER BY total_matches DESC;
        """,
    },
    {
        "id": 21, "level": "Advanced",
        "title": "Weighted performance ranking",
        "question": "Create a comprehensive performance ranking system for players. Combine their batting performance (runs scored, batting average, strike rate), bowling performance (wickets taken, bowling average, economy rate), and fielding performance (catches, stumpings) into a single weighted score. Rank the top performers in each cricket format.",
        "note": "batting = runs*0.01 + avg*0.5 + SR*0.3, bowling = wkts*2 + (50-avg)*0.5 + (6-econ)*2, fielding = catches*3 + stumpings*5 (players who don't bowl/field get 0 there, not penalised)",
        "sql": """
            WITH batting_agg AS (
                SELECT player_id, format,
                       SUM(runs_scored) AS runs,
                       SUM(runs_scored) * 1.0 / NULLIF(SUM(is_out), 0) AS avg_runs,
                       AVG(CASE WHEN balls_faced > 0 THEN runs_scored * 100.0 / balls_faced END) AS sr
                FROM batting_scorecards GROUP BY player_id, format
            ),
            bowling_agg AS (
                SELECT bo.player_id, m.match_type AS format,
                       SUM(bo.wickets_taken) AS wickets,
                       SUM(bo.runs_conceded) * 1.0 / NULLIF(SUM(bo.balls_bowled), 0) * 6 AS economy,
                       SUM(bo.runs_conceded) * 1.0 / NULLIF(SUM(bo.wickets_taken), 0) AS bowling_avg
                FROM bowling_scorecards bo
                JOIN matches m ON bo.match_id = m.match_id
                GROUP BY bo.player_id, m.match_type
            ),
            fielding_agg AS (
                SELECT f.player_id, m.match_type AS format,
                       SUM(f.catches) AS catches, SUM(f.stumpings) AS stumpings
                FROM fielding_stats f
                JOIN matches m ON f.match_id = m.match_id
                GROUP BY f.player_id, m.match_type
            ),
            scored AS (
                SELECT p.full_name, ba.format,
                       (COALESCE(ba.runs, 0) * 0.01 + COALESCE(ba.avg_runs, 0) * 0.5 + COALESCE(ba.sr, 0) * 0.3) AS batting_points,
                       (COALESCE(bo.wickets, 0) * 2 + (50 - COALESCE(bo.bowling_avg, 50)) * 0.5 + (6 - COALESCE(bo.economy, 6)) * 2) AS bowling_points,
                       (COALESCE(fi.catches, 0) * 3 + COALESCE(fi.stumpings, 0) * 5) AS fielding_points
                FROM batting_agg ba
                JOIN players p ON p.player_id = ba.player_id
                LEFT JOIN bowling_agg bo ON bo.player_id = ba.player_id AND bo.format = ba.format
                LEFT JOIN fielding_agg fi ON fi.player_id = ba.player_id AND fi.format = ba.format
            )
            SELECT full_name, format,
                   ROUND(batting_points, 2) AS batting_points,
                   ROUND(bowling_points, 2) AS bowling_points,
                   ROUND(fielding_points, 2) AS fielding_points,
                   ROUND(batting_points + bowling_points + fielding_points, 2) AS total_score,
                   RANK() OVER (PARTITION BY format ORDER BY (batting_points + bowling_points + fielding_points) DESC) AS format_rank
            FROM scored
            ORDER BY format, format_rank
            LIMIT 150;
        """,
    },
    {
        "id": 22, "level": "Advanced",
        "title": "Head-to-head team analysis",
        "question": "Build a head-to-head match prediction analysis between teams. For each pair of teams that have played at least 5 matches against each other in the last 3 years, calculate total matches, wins for each team, average victory margin when each wins, and overall win percentage.",
        "note": "'last 3 years' relative to the newest match_date in this dataset",
        "sql": """
            WITH bounds AS (SELECT MAX(match_date) AS max_date FROM matches),
            recent AS (
                SELECT m.* FROM matches m, bounds
                WHERE m.match_date >= date(bounds.max_date, '-3 years')
            ),
            pairs AS (
                SELECT CASE WHEN team1_id < team2_id THEN team1_id ELSE team2_id END AS team_a,
                       CASE WHEN team1_id < team2_id THEN team2_id ELSE team1_id END AS team_b,
                       winner_id, victory_margin
                FROM recent
            )
            SELECT ta.team_name AS team_a, tb.team_name AS team_b,
                   COUNT(*) AS total_matches,
                   SUM(CASE WHEN winner_id = team_a THEN 1 ELSE 0 END) AS team_a_wins,
                   SUM(CASE WHEN winner_id = team_b THEN 1 ELSE 0 END) AS team_b_wins,
                   ROUND(AVG(CASE WHEN winner_id = team_a THEN victory_margin END), 2) AS team_a_avg_margin,
                   ROUND(AVG(CASE WHEN winner_id = team_b THEN victory_margin END), 2) AS team_b_avg_margin,
                   ROUND(SUM(CASE WHEN winner_id = team_a THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS team_a_win_pct,
                   ROUND(SUM(CASE WHEN winner_id = team_b THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS team_b_win_pct
            FROM pairs
            JOIN teams ta ON ta.team_id = pairs.team_a
            JOIN teams tb ON tb.team_id = pairs.team_b
            GROUP BY team_a, team_b
            HAVING COUNT(*) >= 5
            ORDER BY total_matches DESC;
        """,
    },
    {
        "id": 23, "level": "Advanced",
        "title": "Recent player form",
        "question": "Analyze recent player form and momentum. For each player's last 10 batting performances, calculate average runs in their last 5 vs last 10 matches, recent strike rate trends, number of scores above 50, and a consistency score. Categorize players as \"Excellent Form\", \"Good Form\", \"Average Form\", or \"Poor Form\".",
        "sql": """
            WITH ranked AS (
                SELECT b.player_id, b.runs_scored, b.balls_faced,
                       ROW_NUMBER() OVER (PARTITION BY b.player_id ORDER BY m.match_date DESC) AS rn
                FROM batting_scorecards b
                JOIN matches m ON b.match_id = m.match_id
            ),
            last10 AS (SELECT * FROM ranked WHERE rn <= 10),
            agg AS (
                SELECT player_id,
                       AVG(CASE WHEN rn <= 5 THEN runs_scored END) AS avg_last5,
                       AVG(runs_scored) AS avg_last10,
                       AVG(CASE WHEN balls_faced > 0 THEN runs_scored * 100.0 / balls_faced END) AS recent_sr,
                       SUM(CASE WHEN runs_scored > 50 THEN 1 ELSE 0 END) AS scores_above_50,
                       SQRT(AVG(runs_scored * runs_scored) - AVG(runs_scored) * AVG(runs_scored)) AS consistency_stddev,
                       COUNT(*) AS innings_considered
                FROM last10 GROUP BY player_id
            )
            SELECT p.full_name,
                   ROUND(avg_last5, 2) AS avg_last_5,
                   ROUND(avg_last10, 2) AS avg_last_10,
                   ROUND(recent_sr, 2) AS recent_strike_rate,
                   scores_above_50,
                   ROUND(consistency_stddev, 2) AS consistency_score,
                   CASE
                       WHEN avg_last5 >= 42 AND scores_above_50 >= 3 THEN 'Excellent Form'
                       WHEN avg_last5 >= 28 THEN 'Good Form'
                       WHEN avg_last5 >= 15 THEN 'Average Form'
                       ELSE 'Poor Form'
                   END AS form_category
            FROM agg a
            JOIN players p ON p.player_id = a.player_id
            WHERE innings_considered >= 5
            ORDER BY avg_last5 DESC;
        """,
    },
    {
        "id": 24, "level": "Advanced",
        "title": "Best batting partnerships",
        "question": "Study successful batting partnerships to identify the best player combinations. For pairs of players who have batted together as consecutive batsmen in at least 5 partnerships, calculate average partnership runs, count of partnerships over 50, highest partnership score, and success rate.",
        "note": "partnership runs = combined score of two adjacent batting positions",
        "sql": """
            WITH pos AS (
                SELECT b.match_id, b.team_id, b.format, b.batting_position, b.player_id,
                       b.runs_scored, p.full_name
                FROM batting_scorecards b
                JOIN players p ON b.player_id = p.player_id
            ),
            pairs AS (
                SELECT a.player_id AS player_a, a.full_name AS name_a,
                       c.player_id AS player_b, c.full_name AS name_b,
                       (a.runs_scored + c.runs_scored) AS partnership_runs
                FROM pos a
                JOIN pos c ON a.match_id = c.match_id AND a.team_id = c.team_id
                           AND a.format = c.format AND c.batting_position = a.batting_position + 1
            )
            SELECT name_a, name_b,
                   COUNT(*) AS total_partnerships,
                   ROUND(AVG(partnership_runs), 2) AS avg_partnership_runs,
                   SUM(CASE WHEN partnership_runs > 50 THEN 1 ELSE 0 END) AS partnerships_over_50,
                   MAX(partnership_runs) AS highest_partnership,
                   ROUND(SUM(CASE WHEN partnership_runs > 50 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS success_rate_pct
            FROM pairs
            GROUP BY player_a, player_b
            HAVING COUNT(*) >= 5
            ORDER BY avg_partnership_runs DESC
            LIMIT 50;
        """,
    },
    {
        "id": 25, "level": "Advanced",
        "title": "Career trajectory time-series",
        "question": "Perform a time-series analysis of player performance evolution: quarterly averages for runs and strike rate, quarter-over-quarter comparison, and an overall career phase (\"Career Ascending\", \"Career Declining\", \"Career Stable\"). Only players with data spanning at least 6 quarters and a minimum of 3 matches per quarter.",
        "sql": """
            WITH quarterly AS (
                SELECT b.player_id,
                       strftime('%Y', m.match_date) || '-Q' || ((CAST(strftime('%m', m.match_date) AS INTEGER) - 1) / 3 + 1) AS quarter,
                       COUNT(DISTINCT b.match_id) AS matches_in_qtr,
                       AVG(b.runs_scored) AS avg_runs,
                       AVG(CASE WHEN b.balls_faced > 0 THEN b.runs_scored * 100.0 / b.balls_faced END) AS avg_sr
                FROM batting_scorecards b
                JOIN matches m ON b.match_id = m.match_id
                GROUP BY b.player_id, quarter
            ),
            qualifying AS (
                SELECT player_id FROM quarterly
                WHERE matches_in_qtr >= 3
                GROUP BY player_id HAVING COUNT(DISTINCT quarter) >= 6
            ),
            with_prev AS (
                SELECT q.*, LAG(avg_runs) OVER (PARTITION BY q.player_id ORDER BY quarter) AS prev_avg_runs
                FROM quarterly q
                WHERE q.player_id IN (SELECT player_id FROM qualifying) AND q.matches_in_qtr >= 3
            )
            SELECT p.full_name, w.quarter,
                   ROUND(w.avg_runs, 2) AS avg_runs,
                   ROUND(w.avg_sr, 2) AS avg_strike_rate,
                   CASE
                       WHEN w.prev_avg_runs IS NULL THEN 'N/A'
                       WHEN w.avg_runs > w.prev_avg_runs THEN 'Improving'
                       WHEN w.avg_runs < w.prev_avg_runs THEN 'Declining'
                       ELSE 'Stable'
                   END AS quarter_over_quarter
            FROM with_prev w
            JOIN players p ON p.player_id = w.player_id
            ORDER BY p.full_name, w.quarter;
        """,
        "secondary": {
            "label": "Overall career phase (early vs recent average)",
            "sql": """
                WITH quarterly AS (
                    SELECT b.player_id,
                           strftime('%Y', m.match_date) || '-Q' || ((CAST(strftime('%m', m.match_date) AS INTEGER) - 1) / 3 + 1) AS quarter,
                           COUNT(DISTINCT b.match_id) AS matches_in_qtr,
                           AVG(b.runs_scored) AS avg_runs
                    FROM batting_scorecards b
                    JOIN matches m ON b.match_id = m.match_id
                    GROUP BY b.player_id, quarter
                ),
                qualifying AS (
                    SELECT player_id FROM quarterly
                    WHERE matches_in_qtr >= 3
                    GROUP BY player_id HAVING COUNT(DISTINCT quarter) >= 6
                ),
                ranked AS (
                    SELECT q.*, ROW_NUMBER() OVER (PARTITION BY q.player_id ORDER BY quarter) AS rn,
                           COUNT(*) OVER (PARTITION BY q.player_id) AS total_q
                    FROM quarterly q
                    WHERE q.player_id IN (SELECT player_id FROM qualifying) AND q.matches_in_qtr >= 3
                ),
                halves AS (
                    SELECT player_id,
                           AVG(CASE WHEN rn <= total_q / 2 THEN avg_runs END) AS early_avg,
                           AVG(CASE WHEN rn > total_q / 2 THEN avg_runs END) AS recent_avg
                    FROM ranked GROUP BY player_id
                )
                SELECT p.full_name,
                       ROUND(early_avg, 2) AS early_career_avg_runs,
                       ROUND(recent_avg, 2) AS recent_career_avg_runs,
                       CASE
                           WHEN recent_avg > early_avg * 1.1 THEN 'Career Ascending'
                           WHEN recent_avg < early_avg * 0.9 THEN 'Career Declining'
                           ELSE 'Career Stable'
                       END AS career_phase
                FROM halves h
                JOIN players p ON p.player_id = h.player_id
                ORDER BY recent_avg DESC;
            """,
        },
    },
]

BY_ID = {q["id"]: q for q in QUERIES}
