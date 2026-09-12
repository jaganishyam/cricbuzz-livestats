# check_queries.py
# quick sanity check - runs all 25 queries and prints how many rows each
# one returns. handy after touching generate_data.py to make sure nothing
# ended up empty. run: python check_queries.py

from db_helper import run_query
from sql_queries import QUERIES

failed = []
empty = []

for q in QUERIES:
    try:
        df = run_query(q["sql"])
        n = len(df)
        print(f"Q{q['id']:>2} [{q['level']:<12}] {q['title']:<45} rows={n}" + ("  <-- empty!" if n == 0 else ""))
        if n == 0:
            empty.append(q["id"])
        if "secondary" in q:
            df2 = run_query(q["secondary"]["sql"])
            print(f"     + {q['secondary']['label']:<45} rows={len(df2)}")
            if len(df2) == 0:
                empty.append(f"{q['id']}-secondary")
    except Exception as e:
        print(f"Q{q['id']:>2} FAILED: {e}")
        failed.append(q["id"])

print()
print("failed:", failed)
print("empty:", empty)
