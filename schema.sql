-- schema for the cricbuzz livestats db
-- written for sqlite, but nothing here is sqlite-specific except AUTOINCREMENT
-- (swap that for SERIAL on postgres / AUTO_INCREMENT on mysql if you move off sqlite)

DROP TABLE IF EXISTS fielding_stats;
DROP TABLE IF EXISTS bowling_scorecards;
DROP TABLE IF EXISTS batting_scorecards;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS series;
DROP TABLE IF EXISTS venues;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS teams;

CREATE TABLE teams (
    team_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name    TEXT NOT NULL UNIQUE,
    country      TEXT NOT NULL
);

CREATE TABLE players (
    player_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name      TEXT NOT NULL,
    country        TEXT NOT NULL,
    team_id        INTEGER REFERENCES teams(team_id),
    playing_role   TEXT NOT NULL, -- Batsman / Bowler / All-rounder / Wicket-keeper
    batting_style  TEXT NOT NULL, -- Right-hand bat / Left-hand bat
    bowling_style  TEXT,          -- null if they never bowl
    debut_year     INTEGER
);

CREATE TABLE venues (
    venue_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_name   TEXT NOT NULL,
    city         TEXT NOT NULL,
    country      TEXT NOT NULL,
    capacity     INTEGER NOT NULL
);

CREATE TABLE series (
    series_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    series_name    TEXT NOT NULL,
    host_country   TEXT NOT NULL,
    match_type     TEXT NOT NULL, -- Test / ODI / T20I
    start_date     DATE NOT NULL,
    total_matches  INTEGER NOT NULL
);

CREATE TABLE matches (
    match_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id         INTEGER REFERENCES series(series_id),
    match_desc        TEXT NOT NULL,
    match_type        TEXT NOT NULL,
    team1_id          INTEGER NOT NULL REFERENCES teams(team_id),
    team2_id          INTEGER NOT NULL REFERENCES teams(team_id),
    venue_id          INTEGER NOT NULL REFERENCES venues(venue_id),
    match_date        DATE NOT NULL,
    toss_winner_id    INTEGER REFERENCES teams(team_id),
    toss_decision     TEXT,  -- bat / bowl
    bat_first_team_id INTEGER REFERENCES teams(team_id),
    winner_id         INTEGER REFERENCES teams(team_id),  -- null = draw / no result
    victory_margin    INTEGER,
    victory_type      TEXT   -- runs / wickets
);

CREATE TABLE batting_scorecards (
    scorecard_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id          INTEGER NOT NULL REFERENCES matches(match_id),
    player_id         INTEGER NOT NULL REFERENCES players(player_id),
    team_id           INTEGER NOT NULL REFERENCES teams(team_id),
    format            TEXT NOT NULL,
    batting_position  INTEGER NOT NULL,
    runs_scored       INTEGER NOT NULL DEFAULT 0,
    balls_faced       INTEGER NOT NULL DEFAULT 0,
    fours             INTEGER NOT NULL DEFAULT 0,
    sixes             INTEGER NOT NULL DEFAULT 0,
    is_out            INTEGER NOT NULL DEFAULT 1,  -- 1 = out, 0 = not out
    dismissal_type    TEXT
);

CREATE TABLE bowling_scorecards (
    scorecard_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id        INTEGER NOT NULL REFERENCES matches(match_id),
    player_id       INTEGER NOT NULL REFERENCES players(player_id),
    team_id         INTEGER NOT NULL REFERENCES teams(team_id),
    format          TEXT NOT NULL,
    balls_bowled    INTEGER NOT NULL DEFAULT 0,
    runs_conceded   INTEGER NOT NULL DEFAULT 0,
    wickets_taken   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE fielding_stats (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id    INTEGER NOT NULL REFERENCES matches(match_id),
    player_id   INTEGER NOT NULL REFERENCES players(player_id),
    catches     INTEGER NOT NULL DEFAULT 0,
    stumpings   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_batting_player ON batting_scorecards(player_id);
CREATE INDEX idx_batting_match ON batting_scorecards(match_id);
CREATE INDEX idx_batting_format ON batting_scorecards(format);
CREATE INDEX idx_bowling_player ON bowling_scorecards(player_id);
CREATE INDEX idx_bowling_match ON bowling_scorecards(match_id);
CREATE INDEX idx_fielding_player ON fielding_stats(player_id);
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_teams ON matches(team1_id, team2_id);
CREATE INDEX idx_players_country ON players(country);
