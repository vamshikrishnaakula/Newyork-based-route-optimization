import pandas as pd
import streamlit as st

from bus_ui_server import run_to_dict, solve_payload
from school_bus_optimization_based_on_excel_model import RUNS_RAW


RUN_COLUMNS = [
    "run_id",
    "run_no",
    "school_type_id",
    "category",
    "run_time_min",
    "start_x",
    "start_y",
    "bell_time_min",
    "window_min",
]


def build_default_dataframe() -> pd.DataFrame:
    return pd.DataFrame([run_to_dict(run) for run in RUNS_RAW], columns=RUN_COLUMNS)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg: #f5f1e8;
                --surface: rgba(255, 252, 246, 0.88);
                --surface-strong: #fffdf8;
                --surface-soft: rgba(245, 238, 224, 0.72);
                --border: rgba(84, 72, 56, 0.14);
                --ink: #1f2933;
                --muted: #6b7280;
                --accent: #d97706;
                --accent-deep: #0f766e;
                --accent-soft: #fff3dd;
                --success: #166534;
                --shadow: 0 24px 60px rgba(28, 24, 19, 0.08);
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(15, 118, 110, 0.11), transparent 30%),
                    radial-gradient(circle at top right, rgba(217, 119, 6, 0.14), transparent 26%),
                    linear-gradient(180deg, #fbf7ef 0%, var(--bg) 48%, #efe6d3 100%);
                color: var(--ink);
            }

            .block-container {
                max-width: 1380px;
                padding-top: 2.25rem;
                padding-bottom: 3rem;
            }

            h1, h2, h3 {
                color: var(--ink);
                letter-spacing: -0.02em;
            }

            h1, h2 {
                font-family: Georgia, "Times New Roman", serif;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #17332f 0%, #102522 100%);
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }

            [data-testid="stSidebar"] * {
                color: #f8fafc;
            }

            [data-testid="stSidebar"] .stButton > button {
                border-radius: 999px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                min-height: 46px;
                font-weight: 700;
            }

            [data-testid="stSidebar"] .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                border-color: transparent;
                color: #111827;
                box-shadow: 0 14px 30px rgba(217, 119, 6, 0.32);
            }

            .hero-card,
            .glass-card {
                border: 1px solid var(--border);
                box-shadow: var(--shadow);
                backdrop-filter: blur(14px);
            }

            .hero-card {
                background:
                    linear-gradient(135deg, rgba(15, 118, 110, 0.96) 0%, rgba(19, 78, 74, 0.92) 52%, rgba(12, 37, 42, 0.95) 100%);
                border-radius: 28px;
                padding: 1.8rem 1.9rem;
                color: #f8fafc;
                margin-bottom: 1.25rem;
                overflow: hidden;
                position: relative;
            }

            .hero-card:before,
            .hero-card:after {
                content: "";
                position: absolute;
                border-radius: 999px;
                opacity: 0.28;
            }

            .hero-card:before {
                width: 320px;
                height: 320px;
                right: -90px;
                top: -110px;
                background: radial-gradient(circle, rgba(251, 191, 36, 0.95) 0%, transparent 65%);
            }

            .hero-card:after {
                width: 260px;
                height: 260px;
                left: -100px;
                bottom: -130px;
                background: radial-gradient(circle, rgba(255, 255, 255, 0.28) 0%, transparent 70%);
            }

            .hero-eyebrow {
                display: inline-block;
                padding: 0.32rem 0.78rem;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.14);
                font-size: 0.76rem;
                letter-spacing: 0.16em;
                text-transform: uppercase;
                font-weight: 700;
                margin-bottom: 0.9rem;
            }

            .hero-title {
                font-family: Georgia, "Times New Roman", serif;
                font-size: clamp(2rem, 4vw, 3.6rem);
                line-height: 0.95;
                margin: 0;
                max-width: 720px;
            }

            .hero-copy {
                margin: 0.9rem 0 0;
                max-width: 740px;
                font-size: 1rem;
                color: rgba(248, 250, 252, 0.86);
            }

            .hero-strip {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.9rem;
                margin-top: 1.35rem;
            }

            .hero-chip {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 0.95rem 1rem;
            }

            .hero-chip strong {
                display: block;
                font-size: 1rem;
                margin-bottom: 0.24rem;
            }

            .hero-chip span {
                color: rgba(248, 250, 252, 0.78);
                font-size: 0.9rem;
            }

            .section-title {
                font-family: Georgia, "Times New Roman", serif;
                font-size: 1.35rem;
                margin: 0 0 0.2rem;
            }

            .section-copy {
                color: var(--muted);
                margin: 0 0 1rem;
            }

            .glass-card {
                background: var(--surface);
                border-radius: 24px;
                padding: 1.15rem 1.15rem 1rem;
                margin-bottom: 1rem;
            }

            .metric-card {
                background: linear-gradient(180deg, rgba(255, 253, 248, 0.95) 0%, rgba(247, 241, 230, 0.86) 100%);
                border: 1px solid var(--border);
                border-radius: 22px;
                box-shadow: var(--shadow);
                padding: 1rem 1.05rem;
                min-height: 126px;
            }

            .metric-label {
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                color: var(--muted);
                margin-bottom: 0.5rem;
                font-weight: 700;
            }

            .metric-value {
                font-size: clamp(1.9rem, 3vw, 2.6rem);
                font-weight: 800;
                line-height: 0.95;
                color: var(--ink);
            }

            .metric-note {
                margin-top: 0.55rem;
                color: var(--muted);
                font-size: 0.92rem;
                line-height: 1.35;
            }

            .status-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                border-radius: 999px;
                background: var(--accent-soft);
                color: #7c4700;
                padding: 0.42rem 0.85rem;
                font-size: 0.84rem;
                font-weight: 700;
            }

            .route-card,
            .check-card {
                background: var(--surface-strong);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 0.95rem 1rem;
                margin-bottom: 0.8rem;
            }

            .route-title,
            .check-title {
                font-weight: 800;
                margin-bottom: 0.25rem;
                color: var(--ink);
            }

            .route-meta,
            .check-meta {
                color: var(--muted);
                font-size: 0.93rem;
                line-height: 1.4;
            }

            .route-pill,
            .check-pill {
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                padding: 0.18rem 0.6rem;
                margin-top: 0.7rem;
                font-size: 0.78rem;
                font-weight: 700;
            }

            .route-pill {
                background: rgba(15, 118, 110, 0.12);
                color: var(--accent-deep);
            }

            .check-pill.ok {
                background: rgba(22, 101, 52, 0.12);
                color: var(--success);
            }

            .check-pill.fail {
                background: rgba(185, 28, 28, 0.1);
                color: #b91c1c;
            }

            div[data-testid="stDataEditor"],
            div[data-testid="stDataFrame"] {
                border-radius: 18px;
                overflow: hidden;
                border: 1px solid var(--border);
                background: var(--surface-strong);
            }

            div[data-baseweb="tab-list"] {
                gap: 0.5rem;
            }

            button[data-baseweb="tab"] {
                border-radius: 999px !important;
                background: rgba(255, 255, 255, 0.72) !important;
                border: 1px solid var(--border) !important;
                padding: 0.35rem 0.9rem !important;
            }

            button[data-baseweb="tab"][aria-selected="true"] {
                background: rgba(217, 119, 6, 0.14) !important;
                color: #7c4700 !important;
                border-color: rgba(217, 119, 6, 0.24) !important;
            }

            .stAlert {
                border-radius: 18px;
            }

            @media (max-width: 900px) {
                .hero-strip {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(payload: dict | None) -> None:
    total_runs = payload["total_runs"] if payload else len(st.session_state.runs_df)
    buses_needed = payload["buses_needed"] if payload else "Pending"
    status = payload["status"] if payload else "Ready to optimize"

    st.markdown(
        f"""
        <section class="hero-card">
            <div class="hero-eyebrow">Route Pairing Studio</div>
            <h1 class="hero-title">Design a sharper school bus schedule.</h1>
            <p class="hero-copy">
                Tune bell windows, run lengths, and school coordinates, then let the optimizer build
                cleaner pairings with fewer buses and clearer feasibility checks.
            </p>
            <div class="hero-strip">
                <div class="hero-chip">
                    <strong>{total_runs} active runs</strong>
                    <span>Editable input grid with reset and add-row support.</span>
                </div>
                <div class="hero-chip">
                    <strong>{buses_needed} buses needed</strong>
                    <span>Live summary from the most recent solve result.</span>
                </div>
                <div class="hero-chip">
                    <strong>{status}</strong>
                    <span>Solver feedback stays visible while you refine scenarios.</span>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def coerce_runs(df: pd.DataFrame) -> list[dict]:
    prepared = df.copy()
    prepared["run_id"] = prepared["run_id"].fillna("").astype(str).str.strip()
    prepared["category"] = prepared["category"].fillna("ES").astype(str).str.upper().str.strip()

    numeric_columns = [column for column in RUN_COLUMNS if column not in {"run_id", "category"}]
    for column in numeric_columns:
        prepared[column] = pd.to_numeric(prepared[column], errors="raise")

    return prepared[RUN_COLUMNS].to_dict(orient="records")


def solve_from_records(runs: list[dict]) -> dict:
    return solve_payload(
        [
            (
                run["run_id"],
                int(run["run_no"]),
                int(run["school_type_id"]),
                run["category"],
                float(run["run_time_min"]),
                float(run["start_x"]),
                float(run["start_y"]),
                float(run["bell_time_min"]),
                float(run["window_min"]),
                0.0,
                0.0,
            )
            for run in runs
        ]
    )


def render_metric_card(label: str, value: str | int, note: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(payload: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total runs", payload["total_runs"], "Every run currently included in the solve.")
    with col2:
        render_metric_card("Pairings", payload["pairings_found"], "Direct successor links selected by the model.")
    with col3:
        render_metric_card("Buses needed", payload["buses_needed"], "Estimated fleet requirement after chaining.")
    with col4:
        render_metric_card("Solver status", "Optimal" if "Optimal" in payload["status"] else "Review", payload["status"])


def render_routes(payload: dict) -> None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Bus Routes</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-copy">Each card is one bus chain in the solved plan.</p>',
        unsafe_allow_html=True,
    )

    if payload["routes"]:
        for route in payload["routes"]:
            st.markdown(
                f"""
                <div class="route-card">
                    <div class="route-title">Bus {route["bus"]}</div>
                    <div class="route-meta">{' &rarr; '.join(route["runs"])}</div>
                    <div class="route-pill">{route["run_count"]} run{"s" if route["run_count"] != 1 else ""}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No routes are available yet.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_pairings(payload: dict) -> None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Pairings</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-copy">Selected links between runs with deadhead travel time.</p>',
        unsafe_allow_html=True,
    )

    if payload["pairings"]:
        st.dataframe(pd.DataFrame(payload["pairings"]), use_container_width=True, hide_index=True)
    else:
        st.info("No pairings found. Each run needs its own bus.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_checks(payload: dict) -> None:
    checks = payload["checks"]
    check_rows = [
        ("One successor per run", checks["one_successor_per_run"], "No run starts multiple downstream chains."),
        ("One predecessor per run", checks["one_predecessor_per_run"], "No run is double-booked behind another run."),
        ("Start times within bounds", checks["all_start_times_in_windows"], "All chosen starts stay inside the allowed window."),
        ("Sequencing constraints", checks["all_pairings_sequence"], "Each bus can reach its next run before the next start."),
    ]

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Verification</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-copy">Constraint health checks from the current solution.</p>',
        unsafe_allow_html=True,
    )

    for label, ok, detail in check_rows:
        st.markdown(
            f"""
            <div class="check-card">
                <div class="check-title">{label}</div>
                <div class="check-meta">{detail}</div>
                <div class="check-pill {'ok' if ok else 'fail'}">{'OK' if ok else 'Check needed'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if checks["sequencing"]:
        with st.expander("Sequencing details", expanded=False):
            st.dataframe(pd.DataFrame(checks["sequencing"]), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def initialize_state() -> None:
    if "runs_df" not in st.session_state:
        st.session_state.runs_df = build_default_dataframe()

    if "result_payload" not in st.session_state:
        default_runs = coerce_runs(st.session_state.runs_df)
        st.session_state.result_payload = solve_from_records(default_runs)


def main() -> None:
    st.set_page_config(
        page_title="School Bus Optimizer",
        page_icon="🚌",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()
    initialize_state()

    with st.sidebar:
        st.markdown("### Mission Control")
        st.caption("Adjust the sample, run optimization, and prep the app for deployment.")
        if st.button("Reset sample", use_container_width=True):
            st.session_state.runs_df = build_default_dataframe()
            st.session_state.result_payload = solve_from_records(coerce_runs(st.session_state.runs_df))
        optimize = st.button("Optimize routes", type="primary", use_container_width=True)
        st.markdown("---")
        st.markdown("**What this app gives you**")
        st.markdown("Fewer buses, cleaner route chains, and visible feasibility checks.")

    render_hero(st.session_state.result_payload)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Run Inputs</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-copy">Edit your runs directly in the table, then rerun the optimizer to compare scenarios.</p>',
        unsafe_allow_html=True,
    )

    edited_df = st.data_editor(
        st.session_state.runs_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "category": st.column_config.SelectboxColumn(
                "category",
                options=["ES", "MS", "HS"],
                required=True,
            ),
            "run_no": st.column_config.NumberColumn("run_no", step=1),
            "school_type_id": st.column_config.NumberColumn("school_type_id", step=1),
            "run_time_min": st.column_config.NumberColumn("run_time_min", format="%.1f"),
            "bell_time_min": st.column_config.NumberColumn("bell_time_min", format="%.1f"),
            "window_min": st.column_config.NumberColumn("window_min", format="%.1f"),
        },
    )
    st.session_state.runs_df = edited_df
    st.markdown("</div>", unsafe_allow_html=True)

    if optimize:
        try:
            runs = coerce_runs(edited_df)
            if len(runs) < 2:
                st.error("Add at least two runs before optimizing.")
                return
            st.session_state.result_payload = solve_from_records(runs)
        except Exception as exc:
            st.error(f"Could not optimize runs: {exc}")
            return

    payload = st.session_state.result_payload
    render_metrics(payload)

    st.markdown(
        f'<div class="status-badge">Current solve status: {payload["status"]}</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    left, right = st.columns([1.35, 0.9], gap="large")
    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Operational Tables</div>', unsafe_allow_html=True)
        st.markdown(
            '<p class="section-copy">Review the schedule output and the deadhead matrix side by side.</p>',
            unsafe_allow_html=True,
        )
        schedule_tab, matrix_tab = st.tabs(["Schedule", "Deadhead Matrix"])
        with schedule_tab:
            st.dataframe(pd.DataFrame(payload["schedule"]), use_container_width=True, hide_index=True)
        with matrix_tab:
            matrix_df = pd.DataFrame(payload["deadhead_matrix"], columns=payload["ids"], index=payload["ids"])
            st.dataframe(matrix_df, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        render_routes(payload)
        render_pairings(payload)
        render_checks(payload)


if __name__ == "__main__":
    main()
