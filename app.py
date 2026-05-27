import os
import numpy as np
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import database
import analytics
import generate_mock_data

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Student Performance Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auto-init database ────────────────────────────────────────────────────────
if not os.path.exists(database.DB_FILE):
    database.init_db()
    students, records = generate_mock_data.generate_student_data(500)
    generate_mock_data.save_to_csv(students, records)
    generate_mock_data.populate_database(students, records)


# ── Minimal CSS overrides ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Subtle divider */
hr { border: none; border-top: 1px solid #e5e7eb; margin: 1.25rem 0; }

/* Risk badge */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
}
.badge-red   { background: #fee2e2; color: #b91c1c; }
.badge-amber { background: #fef3c7; color: #b45309; }
.badge-green { background: #dcfce7; color: #15803d; }
</style>
""", unsafe_allow_html=True)

# ── Helper: minimal chart style ───────────────────────────────────────────────
def style_ax(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#d1d5db")
    ax.tick_params(colors="#6b7280", labelsize=9)
    ax.set_facecolor("none")
    return ax

# ── Load data ─────────────────────────────────────────────────────────────────
full_perf_df = database.get_performance_df()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Scorelytics")
    st.caption("Student Performance Dashboard")
    st.divider()

    st.markdown("**Filters**")
    class_opts = ["All Classes"] + sorted(full_perf_df["class_level"].unique().tolist())
    sel_class = st.selectbox("Class", class_opts, label_visibility="collapsed")

    stream_opts = ["All Streams"] + sorted(full_perf_df["stream"].unique().tolist())
    sel_stream = st.selectbox("Stream", stream_opts, label_visibility="collapsed")

    # Dynamically filter subjects based on selected stream
    if sel_stream != "All Streams":
        available_subjects = ["All Subjects"] + analytics.STREAM_SUBJECTS.get(sel_stream, [])
    else:
        available_subjects = ["All Subjects"] + sorted(full_perf_df["subject"].unique().tolist())
    sel_subject = st.selectbox("Subject", available_subjects, label_visibility="collapsed")

    st.divider()
    st.markdown("**Data**")

    if st.button("↺ Regenerate Data", use_container_width=True):
        with st.spinner("Resetting…"):
            st.cache_resource.clear()
            database.reset_db()
            students, records = generate_mock_data.generate_student_data(500)
            generate_mock_data.save_to_csv(students, records)
            generate_mock_data.populate_database(students, records)
        st.rerun()

    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data.csv")
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            st.download_button("⬇ Export CSV", f.read(),
                               file_name="student_data.csv", mime="text/csv",
                               use_container_width=True)

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered_df = full_perf_df.copy()
if sel_class != "All Classes":
    filtered_df = filtered_df[filtered_df["class_level"] == sel_class]
if sel_stream != "All Streams":
    filtered_df = filtered_df[filtered_df["stream"] == sel_stream]
if sel_subject != "All Subjects":
    filtered_df = filtered_df[filtered_df["subject"] == sel_subject]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Student Performance Analytics")
st.caption("Scorelytics — Academic Year 2024–25")
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "Overview", "Student Profiles", "Database"
])

# ═══════════════════════════════════════════════════════════════
# TAB 1 · OVERVIEW
# ═══════════════════════════════════════════════════════════════
with tab1:
    if filtered_df.empty:
        st.info("No records match the selected filters.")
    else:
        stats = analytics.calculate_school_stats(filtered_df)

        # ── KPI row ───────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Students",  stats["total_students"])
        c2.metric("Average Score",   f"{stats['overall_avg']}%")
        c3.metric("Avg Attendance",  f"{stats['overall_attendance']}%")
        c4.metric("Pass Rate",       f"{stats['pass_rate']}%")

        st.divider()

        # ── Charts row 1 ──────────────────────────────────────
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Score Distribution**")
            fig, ax = plt.subplots(figsize=(5, 3), facecolor="none")
            sns.histplot(filtered_df["score"], kde=True, bins=15,
                         color="#3b82f6", alpha=0.6, ax=ax)
            ax.set_xlabel("Score (%)", fontsize=9, color="#6b7280")
            ax.set_ylabel("Count", fontsize=9, color="#6b7280")
            style_ax(ax)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        with col_b:
            st.markdown("**Average Score by Subject**")
            subj_avg = (
                full_perf_df.groupby("subject")["score"]
                .mean()
                .reset_index()
                .sort_values("score", ascending=True)
            )
            fig, ax = plt.subplots(figsize=(5, 3), facecolor="none")
            bars = ax.barh(subj_avg["subject"], subj_avg["score"],
                           color="#3b82f6", height=0.5)
            ax.bar_label(bars, fmt="%.1f", padding=4,
                         fontsize=8, color="#6b7280")
            ax.set_xlabel("Avg Score (%)", fontsize=9, color="#6b7280")
            ax.set_xlim(0, 105)
            style_ax(ax)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        st.divider()

        # ── Charts row 2 ──────────────────────────────────────
        col_c, col_d = st.columns(2)

        with col_c:
            st.markdown("**Attendance vs Score**")
            fig, ax = plt.subplots(figsize=(5, 3.2), facecolor="none")
            sns.regplot(data=filtered_df, x="attendance_rate", y="score",
                        scatter_kws={"s": 10, "alpha": 0.35, "color": "#3b82f6"},
                        line_kws={"color": "#ef4444", "lw": 1.5}, ax=ax)
            ax.set_xlabel("Attendance (%)", fontsize=9, color="#6b7280")
            ax.set_ylabel("Score (%)", fontsize=9, color="#6b7280")
            style_ax(ax)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        with col_d:
            st.markdown("**Study Hours vs Score**")
            fig, ax = plt.subplots(figsize=(5, 3.2), facecolor="none")
            sns.regplot(data=filtered_df, x="study_hours_per_week", y="score",
                        scatter_kws={"s": 10, "alpha": 0.35, "color": "#8b5cf6"},
                        line_kws={"color": "#10b981", "lw": 1.5}, ax=ax)
            ax.set_xlabel("Study Hours / Week", fontsize=9, color="#6b7280")
            ax.set_ylabel("Score (%)", fontsize=9, color="#6b7280")
            style_ax(ax)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

# ═══════════════════════════════════════════════════════════════
# TAB 2 · STUDENT PROFILES
# ═══════════════════════════════════════════════════════════════
with tab2:
    students_df = database.get_students_df()

    if students_df.empty:
        st.info("No students found. Regenerate the database from the sidebar.")
    else:
        # Pre-calculate metrics for filtering
        stu_stats = full_perf_df.groupby("student_id").agg(
            avg_score=("score", "mean"),
            avg_att=("attendance_rate", "mean")
        ).reset_index()

        def compute_student_flags(row):
            risk, _ = analytics.get_risk_status(row["avg_score"], row["avg_att"])
            grade   = analytics.get_grade(row["avg_score"])
            return pd.Series([risk, grade])

        stu_stats[["risk", "grade"]] = stu_stats.apply(compute_student_flags, axis=1)
        students_df = students_df.merge(stu_stats, on="student_id")

        st.markdown("**Filter Students**")
        f1, f2, f3 = st.columns(3)
        risk_filter  = f1.selectbox("Risk Level", ["All", "High Risk", "Medium Risk", "Low Risk"])
        grade_filter = f2.selectbox("Average Grade", ["All", "A", "B", "C", "D", "F (Fail)"])
        att_filter   = f3.selectbox("Attendance", ["All", "Below 75%", "75% & Above"])

        if risk_filter != "All":
            students_df = students_df[students_df["risk"] == risk_filter]
        if grade_filter != "All":
            if grade_filter == "F (Fail)":
                students_df = students_df[students_df["grade"].str.startswith("F")]
            else:
                students_df = students_df[students_df["grade"].str.startswith(grade_filter)]
        if att_filter == "Below 75%":
            students_df = students_df[students_df["avg_att"] < 75.0]
        elif att_filter == "75% & Above":
            students_df = students_df[students_df["avg_att"] >= 75.0]

        st.divider()

        if students_df.empty:
            st.warning("No students match the selected filters.")
        else:
            students_df["label"] = students_df["name"] + " · " + students_df["student_id"]
            label_map = dict(zip(students_df["label"], students_df["student_id"]))

            sel_label = st.selectbox(
                "Search student",
                options=students_df["label"].sort_values(),
            )
            student_id = label_map[sel_label]

            st.divider()

            student_info, perf_df = database.get_student_details(student_id)

            if student_info:
                avg_score      = perf_df["score"].mean()
                avg_attendance = perf_df["attendance_rate"].iloc[0]
                study_hrs      = perf_df["study_hours_per_week"].iloc[0]
                risk, _        = analytics.get_risk_status(avg_score, avg_attendance)

                badge_cls = (
                    "badge-red"   if risk == "High Risk"   else
                    "badge-amber" if risk == "Medium Risk" else
                    "badge-green"
                )

                # ── Profile summary ───────────────────────────────
                col_info, col_chart = st.columns([1, 2])

                with col_info:
                    st.markdown(f"### {student_info['name']}")
                    st.caption(
                        f"**ID:** {student_info['student_id']}  \n"
                        f"**Class:** {student_info['class_level']}  \n"
                        f"**Stream:** {student_info['stream']}  \n"
                        f"**Email:** {student_info['email']}"
                    )
                    st.markdown(
                        f'<span class="badge {badge_cls}">{risk}</span>',
                        unsafe_allow_html=True,
                    )

                    st.divider()

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Avg Score",     f"{avg_score:.1f}%")
                    m2.metric("Attendance",    f"{avg_attendance:.1f}%")
                    m3.metric("Study Hrs/Wk", f"{study_hrs:.1f}")

                    st.divider()

                    # ── PDF report card ───────────────────────────
                    overall_stats_full = analytics.calculate_school_stats(full_perf_df)
                    pdf_path = f"report_card_{student_id}.pdf"

                    if st.button("Generate PDF Report Card", use_container_width=True):
                        with st.spinner("Compiling report…"):
                            analytics.generate_report_card_pdf(
                                student_info, perf_df, overall_stats_full, pdf_path
                            )
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        st.download_button(
                            "⬇ Download Report Card",
                            data=pdf_bytes,
                            file_name=pdf_path,
                            mime="application/pdf",
                            use_container_width=True,
                        )
                        try:
                            os.remove(pdf_path)
                        except OSError:
                            pass

                with col_chart:
                    # ── Subject comparison bar ────────────────────
                    st.markdown("**Subject Scores vs School Average**")
                    subj_stats_df = overall_stats_full.get("subject_stats", pd.DataFrame())
                    subjects      = perf_df["subject"].tolist()
                    stu_scores    = perf_df["score"].tolist()
                    school_avgs   = []
                    for subj in subjects:
                        if not subj_stats_df.empty and subj in subj_stats_df["subject"].values:
                            school_avgs.append(
                                subj_stats_df[subj_stats_df["subject"] == subj]["avg_score"].values[0]
                            )
                        else:
                            school_avgs.append(70.0)

                    x   = np.arange(len(subjects))
                    w   = 0.35
                    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor="none")
                    b1 = ax.bar(x - w/2, stu_scores,  w, label="Student",    color="#3b82f6")
                    b2 = ax.bar(x + w/2, school_avgs, w, label="School Avg", color="#d1d5db")
                    ax.bar_label(b1, fmt="%d", fontsize=8, padding=2, color="#1d4ed8")
                    ax.set_xticks(x)
                    ax.set_xticklabels(subjects, fontsize=8)
                    ax.set_ylabel("Score (%)", fontsize=9, color="#6b7280")
                    ax.set_ylim(0, 110)
                    ax.legend(frameon=False, fontsize=8)
                    style_ax(ax)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()

                st.divider()

                # ── Grade book table ──────────────────────────────
                st.markdown("**Grade Book**")
                gb = perf_df.copy()
                gb["Grade"] = gb["score"].apply(analytics.get_grade)
                gb.columns  = ["Subject", "Score (%)", "Attendance (%)",
                                "Study Hrs/Wk", "Parental Support",
                                "Extracurricular", "Grade"]
                st.dataframe(gb, use_container_width=True, hide_index=True)

            else:
                st.error("Could not load student details.")


# ═══════════════════════════════════════════════════════════════
# TAB 3 · DATABASE EXPLORER
# ═══════════════════════════════════════════════════════════════
with tab3:
    col_schema, col_sql = st.columns([1, 2])

    with col_schema:
        st.markdown("**Schema**")
        st.markdown("""
`students`
- `student_id` PK
- `name`
- `class_level` (Class 11 / Class 12)
- `stream` (Medical / Non-Medical / Commerce / Arts)
- `email`

`performance_records`
- `id` PK AUTO
- `student_id` FK
- `subject`
- `score`
- `attendance_rate`
- `study_hours_per_week`
- `parental_involvement`
- `extracurricular`
        """)

        st.divider()
        st.markdown("**Table Inspector**")
        tbl   = st.selectbox("Table", ["students", "performance_records"])
        limit = st.slider("Rows", 5, 100, 10)

        if st.button("Fetch Rows", use_container_width=True):
            res = database.execute_custom_query(
                f"SELECT * FROM {tbl} LIMIT {limit}"
            )
            if res["type"] == "select":
                st.dataframe(res["data"], use_container_width=True, hide_index=True)
            else:
                st.error("Query failed.")

    with col_sql:
        st.markdown("**SQL Terminal**")
        query = st.text_area(
            "Query",
            value=(
                "SELECT subject,\n"
                "       ROUND(AVG(score), 2)          AS avg_score,\n"
                "       ROUND(AVG(attendance_rate), 2) AS avg_attendance\n"
                "FROM performance_records\n"
                "GROUP BY subject;"
            ),
            height=160,
        )

        if st.button("▶ Run Query", use_container_width=True):
            if not query.strip():
                st.warning("Please enter a SQL query.")
            else:
                with st.spinner("Running…"):
                    res = database.execute_custom_query(query)
                if res["type"] == "select":
                    st.success(f"Returned {len(res['data'])} rows.")
                    st.dataframe(res["data"], use_container_width=True, hide_index=True)
                elif res["type"] == "write":
                    st.success(res["data"])
                    st.cache_resource.clear()
                else:
                    st.error(f"Error: {res['data']}")
