# generate_data.py
#
# builds a sample cricket database - teams, players, venues, series,
# matches and full batting/bowling/fielding scorecards - and loads it
# into whatever db is configured in db_helper.py (sqlite by default).
#
# why fake data at all? the cricbuzz api gives live scores but not the
# years of ball-by-ball history the 25 sql questions need (partnerships,
# quarter by quarter form, toss stats going back years etc), so this
# script fabricates a believable dataset that all 25 queries can actually
# run against. run it once before starting the app:
#
#   python generate_data.py
#
# it drops and rebuilds every table, so re-running just resets things.

import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import text

from db_helper import get_engine

random.seed(42)
np.random.seed(42)

BASE_DIR = Path(__file__).resolve().parent

TEAMS = [
    "India", "Australia", "England", "South Africa", "New Zealand",
    "Pakistan", "Sri Lanka", "Bangladesh", "West Indies", "Afghanistan",
    "Ireland", "Zimbabwe",
]

FORMATS = ["Test", "ODI", "T20I"]

# (name, city, country, capacity) - capacities are roughly real, doesn't
# need to be exact for this
VENUES = [
    ("Melbourne Cricket Ground", "Melbourne", "Australia", 100024),
    ("Eden Gardens", "Kolkata", "India", 66000),
    ("Narendra Modi Stadium", "Ahmedabad", "India", 132000),
    ("Wankhede Stadium", "Mumbai", "India", 33000),
    ("M. Chinnaswamy Stadium", "Bengaluru", "India", 40000),
    ("M.A. Chidambaram Stadium", "Chennai", "India", 50396),
    ("Lord's", "London", "England", 30000),
    ("The Oval", "London", "England", 25500),
    ("Old Trafford", "Manchester", "England", 26000),
    ("Sydney Cricket Ground", "Sydney", "Australia", 48000),
    ("Adelaide Oval", "Adelaide", "Australia", 53500),
    ("Perth Stadium", "Perth", "Australia", 61266),
    ("The Wanderers Stadium", "Johannesburg", "South Africa", 34000),
    ("Newlands", "Cape Town", "South Africa", 25000),
    ("Basin Reserve", "Wellington", "New Zealand", 11600),
    ("Eden Park", "Auckland", "New Zealand", 50224),
    ("Gaddafi Stadium", "Lahore", "Pakistan", 27000),
    ("National Stadium", "Karachi", "Pakistan", 34000),
    ("R. Premadasa Stadium", "Colombo", "Sri Lanka", 35000),
    ("Shere Bangla National Stadium", "Dhaka", "Bangladesh", 25000),
    ("Kensington Oval", "Bridgetown", "West Indies", 28000),
    ("Sabina Park", "Kingston", "West Indies", 20000),
    ("Sheikh Zayed Stadium", "Abu Dhabi", "Afghanistan", 20000),
    ("Malahide Cricket Club Ground", "Dublin", "Ireland", 11500),
    ("Harare Sports Club", "Harare", "Zimbabwe", 10000),
]

# rough first/last name pools per country, just enough variety that
# players don't all look identical. not trying to be 100% authentic.
FIRST_NAMES = {
    "India": ["Rohit", "Virat", "Shubman", "Rishabh", "Ravindra", "Jasprit",
              "Mohammed", "Hardik", "KL", "Suryakumar", "Ajinkya", "Cheteshwar",
              "Yuzvendra", "Kuldeep", "Axar", "Shreyas", "Ishan", "Arshdeep"],
    "Australia": ["Steve", "David", "Pat", "Mitchell", "Josh", "Marnus",
                  "Travis", "Glenn", "Adam", "Nathan", "Cameron", "Alex",
                  "Mitch", "Sean", "Josh", "Matthew", "Ashton", "Marcus"],
    "England": ["Joe", "Ben", "Jos", "Harry", "Jofra", "Mark", "Jonny",
                "Moeen", "Chris", "Sam", "Zak", "Ollie", "Reece", "James",
                "Liam", "Adil", "Jack", "Phil"],
    "South Africa": ["Temba", "Quinton", "Kagiso", "Aiden", "Anrich", "David",
                     "Rassie", "Keshav", "Lungi", "Heinrich", "Wiaan", "Tristan",
                     "Marco", "Reeza", "Dean", "Gerald", "Ryan", "Tabraiz"],
    "New Zealand": ["Kane", "Tom", "Trent", "Devon", "Daryl", "Mitchell",
                    "Tim", "Lockie", "Ish", "Glenn", "Matt", "Will",
                    "Finn", "Rachin", "Michael", "Kyle", "Adam", "Henry"],
    "Pakistan": ["Babar", "Shaheen", "Mohammad", "Shadab", "Fakhar", "Imam",
                 "Naseem", "Haris", "Shan", "Sarfaraz", "Abdullah", "Iftikhar",
                 "Usman", "Hasan", "Saud", "Khushdil", "Mohammad", "Zaman"],
    "Sri Lanka": ["Kusal", "Dimuth", "Angelo", "Wanindu", "Dushmantha",
                  "Charith", "Pathum", "Dasun", "Maheesh", "Dhananjaya",
                  "Kasun", "Nissanka", "Chamika", "Lahiru", "Bhanuka",
                  "Avishka", "Dilshan", "Matheesha"],
    "Bangladesh": ["Shakib", "Litton", "Mushfiqur", "Mehidy", "Taskin",
                   "Najmul", "Towhid", "Mahmudullah", "Nasum", "Shoriful",
                   "Tanzid", "Hasan", "Shamim", "Rishad", "Mustafizur",
                   "Zakir", "Afif", "Ebadot"],
    "West Indies": ["Nicholas", "Shai", "Jason", "Kyle", "Alzarri", "Shimron",
                    "Andre", "Jayden", "Roston", "Akeal", "Rovman", "Gudakesh",
                    "Sherfane", "Romario", "Brandon", "Keacy", "Alick", "Obed"],
    "Afghanistan": ["Rashid", "Mohammad", "Rahmanullah", "Ibrahim", "Naveen",
                    "Mujeeb", "Fazalhaq", "Azmatullah", "Gulbadin", "Najibullah",
                    "Hashmatullah", "Rahmat", "Karim", "Noor", "Sediqullah",
                    "Zia-ur-Rehman", "Darwish", "Nangeyalia"],
    "Ireland": ["Paul", "Andrew", "Harry", "Curtis", "Mark", "Lorcan",
                "Craig", "George", "Barry", "Gareth", "Simi", "Ross",
                "Josh", "Ben", "Fionn", "Neil", "Stephen", "Graham"],
    "Zimbabwe": ["Craig", "Sikandar", "Sean", "Ryan", "Blessing", "Wessly",
                 "Innocent", "Tony", "Tadiwanashe", "Brian", "Milton",
                 "Richard", "Clive", "Wellington", "Luke", "Tashinga",
                 "Trevor", "Munashe"],
}

LAST_NAMES = {
    "India": ["Sharma", "Kohli", "Gill", "Pant", "Jadeja", "Bumrah", "Shami",
              "Pandya", "Rahul", "Yadav", "Rahane", "Pujara", "Chahal",
              "Kuldeep", "Patel", "Iyer", "Kishan", "Singh"],
    "Australia": ["Smith", "Warner", "Cummins", "Starc", "Hazlewood", "Labuschagne",
                  "Head", "Maxwell", "Zampa", "Lyon", "Green", "Carey",
                  "Marsh", "Abbott", "Inglis", "Wade", "Agar", "Stoinis"],
    "England": ["Root", "Stokes", "Buttler", "Brook", "Archer", "Wood",
                "Bairstow", "Ali", "Woakes", "Curran", "Crawley", "Pope",
                "Topley", "Anderson", "Livingstone", "Rashid", "Leach", "Salt"],
    "South Africa": ["Bavuma", "de Kock", "Rabada", "Markram", "Nortje",
                     "Miller", "van der Dussen", "Maharaj", "Ngidi", "Klaasen",
                     "Mulder", "Stubbs", "Jansen", "Hendricks", "Elgar",
                     "Coetzee", "Rickelton", "Shamsi"],
    "New Zealand": ["Williamson", "Latham", "Boult", "Conway", "Cleaver",
                    "Santner", "Southee", "Ferguson", "Sodhi", "Phillips",
                    "Henry", "Young", "Allen", "Ravindra", "Bracewell",
                    "Jamieson", "Chapman", "Sears"],
    "Pakistan": ["Azam", "Afridi", "Rizwan", "Khan", "Zaman", "Ul Haq",
                 "Shah", "Rauf", "Farhan", "Ahmed", "Shafique", "Nawaz",
                 "Khan", "Ali", "Shakeel", "Wasim", "Hasnain", "Iqbal"],
    "Sri Lanka": ["Mendis", "Karunaratne", "Mathews", "Hasaranga", "Chameera",
                  "Asalanka", "Nissanka", "Shanaka", "Theekshana", "de Silva",
                  "Rajitha", "Fernando", "Chandimal", "Kumara", "Rajapaksa",
                  "Fernando", "Madushanka", "Pathirana"],
    "Bangladesh": ["Al Hasan", "Das", "Rahim", "Hasan", "Ahmed", "Sarkar",
                   "Hridoy", "Riyad", "Ahmed", "Islam", "Tamim", "Mahmud",
                   "Hossain", "Rana", "Rahman", "Hasan", "Ahmed", "Hossain"],
    "West Indies": ["Pooran", "Hope", "Holder", "Mayers", "Joseph", "Hetmyer",
                    "Russell", "Seales", "Chase", "Hosein", "Powell", "Motie",
                    "Pierre", "Shepherd", "King", "Carty", "Athanaze", "Bishop"],
    "Afghanistan": ["Khan", "Nabi", "Gurbaz", "Zadran", "Ul Haq", "Ur Rahman",
                    "Farooqi", "Omarzai", "Naib", "Zadran", "Zazai", "Shah",
                    "Janat", "Ahmadi", "Zadran", "Baraki", "Danish", "Kharote"],
    "Ireland": ["Stirling", "Balbirnie", "Tector", "Campher", "Adair",
                "Tucker", "Young", "Dockrell", "McCarthy", "Delany",
                "Singh", "Adair", "Little", "White", "Hand", "Rock",
                "Doheny", "Humphreys"],
    "Zimbabwe": ["Ervine", "Raza", "Williams", "Burl", "Muzarabani", "Madande",
                 "Chakabva", "Marumani", "Nyauchi", "Ngarava", "Mayers",
                 "Kaia", "Munyonga", "Chivanga", "Musakanda", "Mutombodzi",
                 "Chatara", "Madziva"],
}

ROLE_WEIGHTS = {"Batsman": 0.32, "Bowler": 0.30, "All-rounder": 0.20, "Wicket-keeper": 0.18}

BOWLING_STYLES = [
    "Right-arm fast", "Right-arm fast-medium", "Right-arm medium",
    "Right-arm off break", "Right-arm leg break", "Left-arm fast",
    "Left-arm fast-medium", "Left-arm orthodox", "Left-arm wrist spin",
]

START_DATE = date(2019, 1, 1)
END_DATE = date(2026, 8, 15)  # treat this as "today" for the sample data
PLAYERS_PER_TEAM = 20
XI_STABILITY = 0.85  # how often we reuse the same settled XI vs rotate someone in


def days_between(d1, d2):
    return (d2 - d1).days


def build_teams():
    return pd.DataFrame({
        "team_id": range(1, len(TEAMS) + 1),
        "team_name": TEAMS,
        "country": TEAMS,
    })


def pick_role():
    roles, weights = zip(*ROLE_WEIGHTS.items())
    return random.choices(roles, weights=weights, k=1)[0]


def build_players(teams):
    rows = []
    pid = 1
    for _, team in teams.iterrows():
        country = team["country"]
        firsts, lasts = FIRST_NAMES[country], LAST_NAMES[country]
        used = set()
        for _ in range(PLAYERS_PER_TEAM):
            for _try in range(20):
                name = random.choice(firsts) + " " + random.choice(lasts)
                if name not in used:
                    used.add(name)
                    break

            role = pick_role()
            bat_style = random.choices(["Right-hand bat", "Left-hand bat"], weights=[0.65, 0.35])[0]

            if role == "Batsman":
                bowl_style = None if random.random() < 0.7 else random.choice(BOWLING_STYLES)
            elif role == "Wicket-keeper":
                bowl_style = None
            else:
                bowl_style = random.choice(BOWLING_STYLES)

            # these two numbers drive how the player performs in the sim -
            # think of them as "true skill" that the match-by-match numbers
            # scatter around
            if role == "Batsman":
                bat_skill, bowl_skill = np.random.normal(40, 8), None
            elif role == "Wicket-keeper":
                bat_skill, bowl_skill = np.random.normal(32, 7), None
            elif role == "All-rounder":
                bat_skill, bowl_skill = np.random.normal(30, 6), np.random.normal(29, 5)
            else:
                bat_skill, bowl_skill = np.random.normal(14, 6), np.random.normal(26, 4)

            rows.append({
                "player_id": pid, "full_name": name, "country": country,
                "team_id": team["team_id"], "playing_role": role,
                "batting_style": bat_style, "bowling_style": bowl_style,
                "debut_year": random.randint(2012, 2023),
                "_bat_skill": max(bat_skill, 8.0), "_bowl_skill": bowl_skill,
            })
            pid += 1
    return pd.DataFrame(rows)


def build_venues():
    return pd.DataFrame({
        "venue_id": range(1, len(VENUES) + 1),
        "venue_name": [v[0] for v in VENUES],
        "city": [v[1] for v in VENUES],
        "country": [v[2] for v in VENUES],
        "capacity": [v[3] for v in VENUES],
    })


def home_venue(venues, country):
    local = venues[venues["country"] == country]
    if len(local) and random.random() < 0.8:
        return int(local.sample(1).iloc[0]["venue_id"])
    return int(venues.sample(1).iloc[0]["venue_id"])


def add_match(rows, match_id, series_id, fmt, team1, team2, venue_id, match_dt, game_no, total_games, team_name_of):
    toss_winner = random.choice([team1, team2])
    bat_first_bias = {"Test": 0.62, "ODI": 0.48, "T20I": 0.45}[fmt]
    toss_decision = "bat" if random.random() < bat_first_bias else "bowl"
    bat_first = toss_winner if toss_decision == "bat" else (team2 if toss_winner == team1 else team1)
    chasing = team2 if bat_first == team1 else team1

    is_draw = (fmt == "Test") and (random.random() < 0.12)
    if is_draw:
        winner, margin, vtype = None, None, None
    else:
        # small edge to bat-first side in tests, chasing side in white ball -
        # not perfectly "real" but gives some texture to the numbers
        if fmt == "Test":
            winner = bat_first if random.random() < 0.52 else chasing
        else:
            winner = chasing if random.random() < 0.52 else bat_first

        if winner == bat_first:
            vtype = "runs"
            margin = random.randint(5, 280) if fmt == "Test" else (
                random.randint(5, 150) if fmt == "ODI" else random.randint(3, 60))
        else:
            vtype = "wickets"
            margin = random.randint(1, 10)

    rows.append({
        "match_id": match_id, "series_id": series_id,
        "match_desc": f"{team_name_of[team1]} vs {team_name_of[team2]}, {fmt} {game_no} of {total_games}",
        "match_type": fmt, "team1_id": team1, "team2_id": team2, "venue_id": venue_id,
        "match_date": match_dt.isoformat(), "toss_winner_id": toss_winner,
        "toss_decision": toss_decision, "bat_first_team_id": bat_first,
        "winner_id": winner, "victory_margin": margin, "victory_type": vtype,
    })
    return match_id + 1


def build_series_and_matches(teams, venues):
    series_rows, match_rows = [], []
    series_id, match_id = 1, 1
    team_ids = teams["team_id"].tolist()
    team_name_of = dict(zip(teams["team_id"], teams["country"]))
    span = days_between(START_DATE, END_DATE)

    # normal random tour schedule, this is most of the dataset
    for _ in range(95):
        fmt = random.choices(FORMATS, weights=[0.28, 0.34, 0.38])[0]
        host, away = random.sample(team_ids, 2)
        host_country = team_name_of[host]
        start_dt = START_DATE + timedelta(days=random.randint(0, span - 40))
        n_games = {"Test": random.choice([2, 2, 3, 3, 4, 5]),
                   "ODI": random.choice([3, 3, 3, 5, 5]),
                   "T20I": random.choice([3, 3, 5, 5])}[fmt]
        gap = {"Test": 5, "ODI": 3, "T20I": 2}[fmt]

        series_rows.append({
            "series_id": series_id,
            "series_name": f"{host_country} vs {team_name_of[away]} {fmt} Series {start_dt.year}",
            "host_country": host_country, "match_type": fmt,
            "start_date": start_dt.isoformat(), "total_matches": n_games,
        })

        venue_id = home_venue(venues, host_country)
        cur = start_dt
        for g in range(n_games):
            match_id = add_match(match_rows, match_id, series_id, fmt, host, away,
                                  venue_id, cur, g + 1, n_games, team_name_of)
            cur += timedelta(days=gap + random.randint(0, 2))
        series_id += 1

    # a handful of rivalries concentrated in the last 3 years so the
    # head-to-head query (q22) actually has pairs with 5+ recent meetings
    rivalries = [("India", "Australia"), ("India", "England"), ("Australia", "England"),
                 ("India", "Pakistan"), ("India", "South Africa")]
    recent_start = END_DATE - timedelta(days=3 * 365 - 30)
    name_to_id = {v: k for k, v in team_name_of.items()}
    for a, b in rivalries:
        for fmt in ["ODI", "T20I"]:
            n_games = random.choice([5, 6, 7])
            start_dt = recent_start + timedelta(days=random.randint(0, max(days_between(recent_start, END_DATE) - 20, 1)))
            venue_id = home_venue(venues, a)
            series_rows.append({
                "series_id": series_id, "series_name": f"{a} vs {b} {fmt} Rivalry Series {start_dt.year}",
                "host_country": a, "match_type": fmt,
                "start_date": start_dt.isoformat(), "total_matches": n_games,
            })
            cur = start_dt
            gap = {"ODI": 3, "T20I": 2}[fmt]
            for g in range(n_games):
                match_id = add_match(match_rows, match_id, series_id, fmt,
                                      name_to_id[a], name_to_id[b], venue_id, cur,
                                      g + 1, n_games, team_name_of)
                cur += timedelta(days=gap)
            series_id += 1

    # and a few series explicitly in 2024 for q8
    for _ in range(8):
        fmt = random.choice(FORMATS)
        host, away = random.sample(team_ids, 2)
        host_country = team_name_of[host]
        start_dt = date(2024, random.randint(1, 12), random.randint(1, 28))
        n_games = random.choice([3, 3, 5])
        series_rows.append({
            "series_id": series_id, "series_name": f"{host_country} vs {team_name_of[away]} {fmt} Series 2024",
            "host_country": host_country, "match_type": fmt,
            "start_date": start_dt.isoformat(), "total_matches": n_games,
        })
        venue_id = home_venue(venues, host_country)
        cur = start_dt
        gap = {"Test": 5, "ODI": 3, "T20I": 2}[fmt]
        for g in range(n_games):
            match_id = add_match(match_rows, match_id, series_id, fmt, host, away,
                                  venue_id, cur, g + 1, n_games, team_name_of)
            cur += timedelta(days=gap)
        series_id += 1

    return pd.DataFrame(series_rows), pd.DataFrame(match_rows)


def settled_xis(players):
    # each team gets one "usual" batting order (keeper up top, bowlers at
    # the tail) that we reuse most matches - keeps partnerships and venue
    # bowling stats from being pure noise
    xis = {}
    order = {"Wicket-keeper": 1, "Batsman": 0, "All-rounder": 2, "Bowler": 3}
    for team_id, grp in players.groupby("team_id"):
        grp = grp.copy()
        grp["sort_key"] = grp["playing_role"].map(order)
        xi = grp.sort_values("sort_key").head(11)
        rest = grp[~grp["player_id"].isin(xi["player_id"])]
        xis[team_id] = {"xi": xi["player_id"].tolist(), "reserves": rest["player_id"].tolist()}
    return xis


def pick_lineup(team_id, xis):
    info = xis[team_id]
    if random.random() < XI_STABILITY or not info["reserves"]:
        return list(info["xi"])
    lineup = list(info["xi"])
    for _ in range(random.choice([1, 1, 2])):
        lineup[random.randrange(len(lineup))] = random.choice(info["reserves"])
    return lineup


def sim_batting(lineup, players, match_id, team_id, fmt, out_rows):
    sr_base = {"Test": 55, "ODI": 85, "T20I": 130}[fmt]
    ball_cap = {"Test": 320, "ODI": 150, "T20I": 62}[fmt]

    for pos, pid in enumerate(lineup, start=1):
        p = players[pid]
        skill = p["_bat_skill"]
        pos_factor = 1.0 if pos <= 6 else max(0.25, 1.0 - 0.14 * (pos - 6))  # tail-enders don't get many runs
        mean_runs = max(2.0, skill * pos_factor * random.uniform(0.55, 1.35))
        runs = int(round(np.random.exponential(mean_runs)))
        runs = min(runs, ball_cap * 2)

        out = 1 if random.random() < 0.82 else 0
        sr = max(25, np.random.normal(sr_base * (0.9 if pos > 7 else 1.0), sr_base * 0.18))
        balls = int(round(runs * 100.0 / sr)) if runs > 0 else random.randint(0, 6)
        balls = max(balls, 1 if runs > 0 else 0)
        balls = min(balls, ball_cap)

        fours = min(int(runs * random.uniform(0.28, 0.5) / 4), balls) if runs >= 4 else 0
        sixes = min(int(runs * random.uniform(0.05, 0.18) / 6), max(balls - fours, 0)) if runs >= 6 else 0

        dismissal = None
        if out:
            dismissal = random.choices(
                ["Caught", "Bowled", "LBW", "Run Out", "Stumped", "Caught & Bowled"],
                weights=[0.45, 0.2, 0.15, 0.1, 0.05, 0.05])[0]

        out_rows.append({
            "match_id": match_id, "player_id": pid, "team_id": team_id, "format": fmt,
            "batting_position": pos, "runs_scored": runs, "balls_faced": balls,
            "fours": fours, "sixes": sixes, "is_out": out, "dismissal_type": dismissal,
        })


def sim_bowling(lineup, players, match_id, team_id, fmt, out_rows):
    max_overs = {"Test": 34, "ODI": 10, "T20I": 4}[fmt]
    bowl_chance = {"Bowler": 0.96, "All-rounder": 0.8, "Wicket-keeper": 0.02, "Batsman": 0.12}

    bowlers = [pid for pid in lineup if random.random() < bowl_chance[players[pid]["playing_role"]]]
    if len(bowlers) < 4:
        extra = [pid for pid in lineup if pid not in bowlers]
        random.shuffle(extra)
        bowlers += extra[:max(0, 5 - len(bowlers))]

    for pid in bowlers:
        p = players[pid]
        bowl_skill = p["_bowl_skill"] if p["_bowl_skill"] is not None else 55.0
        overs = random.uniform(4, max_overs) if fmt == "Test" else random.uniform(1.5, max_overs)
        balls = int(round(overs * 6))
        if balls <= 0:
            continue

        econ_base = {"Test": 3.1, "ODI": 5.1, "T20I": 7.6}[fmt]
        skill_factor = max(0.55, min(1.6, bowl_skill / 28.0))
        economy = max(2.0, np.random.normal(econ_base * skill_factor, econ_base * 0.22))
        runs_conceded = int(round(economy * balls / 6.0))

        wicket_rate = max(0.01, 0.55 / skill_factor)
        wickets = min(int(np.random.poisson(max(wicket_rate * (balls / 6.0), 0.05))), 10)

        out_rows.append({
            "match_id": match_id, "player_id": pid, "team_id": team_id, "format": fmt,
            "balls_bowled": balls, "runs_conceded": runs_conceded, "wickets_taken": wickets,
        })


def sim_fielding(lineup, players, match_id, out_rows):
    for pid in lineup:
        role = players[pid]["playing_role"]
        catches = int(np.random.poisson(0.55 if role == "Wicket-keeper" else 0.35))
        stumpings = int(np.random.poisson(0.12)) if role == "Wicket-keeper" else 0
        if catches or stumpings:
            out_rows.append({"match_id": match_id, "player_id": pid, "catches": catches, "stumpings": stumpings})


def build_scorecards(matches, players, xis):
    players_by_id = players.set_index("player_id").to_dict("index")
    batting_rows, bowling_rows, fielding_rows = [], [], []

    for _, m in matches.iterrows():
        fmt = m["match_type"]
        for team_id in (m["team1_id"], m["team2_id"]):
            lineup = pick_lineup(int(team_id), xis)
            sim_batting(lineup, players_by_id, m["match_id"], team_id, fmt, batting_rows)
            sim_bowling(lineup, players_by_id, m["match_id"], team_id, fmt, bowling_rows)
            sim_fielding(lineup, players_by_id, m["match_id"], fielding_rows)

    batting_df = pd.DataFrame(batting_rows)
    bowling_df = pd.DataFrame(bowling_rows)
    fielding_df = pd.DataFrame(fielding_rows)
    fielding_df.insert(0, "id", range(1, len(fielding_df) + 1))
    return batting_df, bowling_df, fielding_df


def load_schema(engine):
    sql = (BASE_DIR / "schema.sql").read_text()
    with engine.begin() as conn:
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))


def push(df, table, engine, drop=None):
    if drop:
        df = df.drop(columns=[c for c in drop if c in df.columns])
    df.to_sql(table, engine, if_exists="append", index=False)


def main():
    print("building teams / players / venues...")
    teams = build_teams()
    players = build_players(teams)
    venues = build_venues()

    print("scheduling series + matches...")
    series, matches = build_series_and_matches(teams, venues)
    print(f"  {len(series)} series, {len(matches)} matches")

    xis = settled_xis(players)

    print("simulating scorecards (this is the slow bit)...")
    batting_df, bowling_df, fielding_df = build_scorecards(matches, players, xis)
    print(f"  {len(batting_df)} batting rows, {len(bowling_df)} bowling rows, {len(fielding_df)} fielding rows")

    engine = get_engine()
    print("rebuilding schema...")
    load_schema(engine)

    print("loading tables...")
    push(teams, "teams", engine)
    push(players, "players", engine, drop=["_bat_skill", "_bowl_skill"])
    push(venues, "venues", engine)
    push(series, "series", engine)
    push(matches, "matches", engine)
    push(batting_df, "batting_scorecards", engine)
    push(bowling_df, "bowling_scorecards", engine)
    push(fielding_df, "fielding_stats", engine)

    print("done - database is ready.")


if __name__ == "__main__":
    main()
