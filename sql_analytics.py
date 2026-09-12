# sql_analytics.py - "SQL Queries & Analytics Page"
# picks a question from sql_queries.py, runs it, shows the result +
# a quick auto chart when that makes sense.

import plotly.express as px
import streamlit as st

from db_helper import run_query, db_ready
from sql_queries import QUERIES, BY_ID

DOT = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}


def render():
    st.header("🧮 SQL Queries & Analytics")
    st.caption("25 queries, beginner to advanced, run live against the database.")

    if not db_ready():
        st.error("Database isn't seeded yet.")
        st.code("python generate_data.py", language="bash")
        return

    level = st.radio("Difficulty", ["All", "Beginner", "Intermediate", "Advanced"], horizontal=True)
    pool = QUERIES if level == "All" else [q for q in QUERIES if q["level"] == level]

    labels = {q["id"]: f"{DOT[q['level']]} Q{q['id']} - {q['title']}" for q in pool}
    qid = st.selectbox("Pick a question", list(labels), format_func=lambda i: labels[i])
    q = BY_ID[qid]

    st.subheader(f"Q{q['id']}. {q['title']}")
    st.write(q["question"])
    if q.get("note"):
        st.caption("Note: " + q["note"])

    with st.expander("show sql"):
        st.code(q["sql"].strip(), language="sql")

    try:
        df = run_query(q["sql"])
    except Exception as e:
        st.error(f"query blew up: {e}")
        return

    st.success(f"{len(df)} rows")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Download CSV", df.to_csv(index=False).encode(), f"q{q['id']}.csv", "text/csv")

    # only auto-chart when it's obviously a "ranking" style result -
    # one text column + one number column, not too many rows
    if not df.empty and len(df) <= 30:
        nums = df.select_dtypes("number").columns.tolist()
        txts = [c for c in df.columns if c not in nums]
        if nums and txts and df[txts[0]].nunique() == len(df):
            chart_df = df[[txts[0], nums[0]]].sort_values(nums[0])
            fig = px.bar(chart_df, x=nums[0], y=txts[0], orientation="h",
                         color_discrete_sequence=["#1B5E20"])
            st.plotly_chart(fig, use_container_width=True)

    if "secondary" in q:
        st.markdown(f"**{q['secondary']['label']}**")
        with st.expander("show sql"):
            st.code(q["secondary"]["sql"].strip(), language="sql")
        df2 = run_query(q["secondary"]["sql"])
        st.dataframe(df2, use_container_width=True, hide_index=True)
