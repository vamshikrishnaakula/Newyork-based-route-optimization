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
                --surface: #ffffff;
                --page: #f6f8f6;
                --border: #d7ded7;
                --text: #162117;
                --muted: #6c776d;
                --soft: #eef5ee;
                --ok-bg: #dcfce7;
                --ok-text: #166534;
            }

            .stApp {
                background: var(--page);
                color: var(--text);
            }

            .block-container {
                max-width: 1820px;
                padding-top: 0.35rem;
                padding-bottom: 1rem;
            }

            [data-testid="stSidebar"],
            [data-testid="collapsedControl"] {
                display: none;
            }

            .app-kicker {
                color: #2d6b41;
                font-size: 0.53rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 0.05rem;
            }

            .app-title {
                font-size: 1.8rem;
                font-weight: 700;
                line-height: 1.1;
                margin: 0 0 0.25rem;
            }

            .summary-card,
            .section-shell {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 4px;
            }

            .summary-card {
                min-height: 52px;
                padding: 0.38rem 0.5rem;
            }

            .metric-label {
                color: var(--muted);
                font-size: 0.52rem;
                margin-bottom: 0.15rem;
            }

            .metric-value {
                font-size: 1.35rem;
                font-weight: 700;
                line-height: 1;
            }

            .metric-status {
                font-size: 0.62rem;
                font-weight: 600;
                line-height: 1.35;
                white-space: normal;
                word-break: break-word;
            }

            .section-shell {
                padding: 0.32rem 0.42rem 0.38rem;
                margin-top: 0.35rem;
            }

            .section-title {
                font-size: 0.75rem;
                font-weight: 700;
                margin: 0;
                line-height: 1.2;
            }

            .section-copy {
                color: var(--muted);
                font-size: 0.53rem;
                line-height: 1.25;
                margin: 0.05rem 0 0;
            }

            .item-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 4px;
                padding: 0.36rem 0.42rem;
                margin-bottom: 0.24rem;
            }

            .item-title {
                font-size: 0.63rem;
                font-weight: 700;
                margin-bottom: 0.1rem;
            }

            .item-copy {
                color: var(--muted);
                font-size: 0.54rem;
                line-height: 1.25;
            }

            .ok-chip {
                display: inline-block;
                margin-top: 0.18rem;
                padding: 0.06rem 0.28rem;
                border-radius: 4px;
                background: var(--ok-bg);
                color: var(--ok-text);
                font-size: 0.5rem;
                font-weight: 700;
            }

            .stButton > button {
                min-height: 26px;
                padding: 0.1rem 0.45rem;
                border-radius: 4px;
                border: 1px solid var(--border);
                background: var(--surface);
                font-size: 0.6rem;
                font-weight: 600;
            }

            div[data-testid="stDataEditor"],
            div[data-testid="stDataFrame"] {
                border: 1px solid var(--border);
                border-radius: 4px;
                overflow: hidden;
                background: var(--surface);
            }

            .stAlert {
                border-radius: 4px;
            }
        </style>
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


def initialize_state() -> None:
    if "runs_df" not in st.session_state:
        st.session_state.runs_df = build_default_dataframe()
    if "result_payload" not in st.session_state:
        st.session_state.result_payload = solve_from_records(coerce_runs(st.session_state.runs_df))


def section_header(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-shell">
            <div class="section-title">{title}</div>
            <div class="section-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown('<div class="app-kicker">MILP ROUTE PAIRING</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">School Bus Optimizer</div>', unsafe_allow_html=True)


def render_summary(payload: dict) -> None:
    columns = st.columns([1, 1, 1, 1.6], gap="small")
    rows = [
        ("Total runs", payload["total_runs"], False),
        ("Pairings", payload["pairings_found"], False),
        ("Buses needed", payload["buses_needed"], False),
        ("Status", payload["status"], True),
    ]
    for col, (label, value, is_status) in zip(columns, rows):
        with col:
            klass = "metric-status" if is_status else "metric-value"
            st.markdown(
                f"""
                <div class="summary-card">
                    <div class="metric-label">{label}</div>
                    <div class="{klass}">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_routes(payload: dict) -> None:
    section_header("Bus Routes", "Each chain is one bus assignment.")
    if not payload["routes"]:
        st.info("No bus routes assigned.")
        return

    for route in payload["routes"]:
        st.markdown(
            f"""
            <div class="item-card">
                <div class="item-title">Bus {route["bus"]}</div>
                <div class="item-copy">{' → '.join(route["runs"])}</div>
                <div class="ok-chip">{route["run_count"]} run{"s" if route["run_count"] != 1 else ""}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_pairings(payload: dict) -> None:
    section_header("Pairings", "Direct links selected by the optimizer.")
    if not payload["pairings"]:
        st.info("No pairings found. Each run needs its own bus.")
        return

    for pairing in payload["pairings"]:
        st.markdown(
            f"""
            <div class="item-card">
                <div class="item-title">{pairing["from"]} → {pairing["to"]}</div>
                <div class="item-copy">Deadhead {pairing["deadhead_min"]:.2f} min</div>
                <div class="ok-chip">Linked</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_checks(payload: dict) -> None:
    checks = payload["checks"]
    items = [
        ("One successor per run", checks["one_successor_per_run"], "No run starts two later runs."),
        ("One predecessor per run", checks["one_predecessor_per_run"], "No run is assigned to two previous runs."),
        ("Start windows", checks["all_start_times_in_windows"], "Every start time stays inside the allowed window."),
        ("Sequencing", checks["all_pairings_sequence"], "Each paired bus reaches the next run on time."),
    ]

    section_header("Verification", "Constraint checks from the solved schedule.")
    for label, ok, detail in items:
        st.markdown(
            f"""
            <div class="item-card">
                <div class="item-title">{label}</div>
                <div class="item-copy">{detail}</div>
                <div class="ok-chip">{'OK' if ok else 'Check needed'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(page_title="School Bus Optimizer", page_icon="🚌", layout="wide")
    inject_styles()
    initialize_state()

    render_header()
    render_summary(st.session_state.result_payload)

    section_header("Run Inputs", "Adjust run times, bell windows, and coordinates, then optimize.")
    toolbar = st.columns([11.2, 1.1, 1.2], gap="small")
    with toolbar[0]:
        st.write("")
    with toolbar[1]:
        reset = st.button("Reset", use_container_width=True)
    with toolbar[2]:
        optimize = st.button("Optimize", use_container_width=True)

    if reset:
        st.session_state.runs_df = build_default_dataframe()
        st.session_state.result_payload = solve_from_records(coerce_runs(st.session_state.runs_df))

    edited_df = st.data_editor(
        st.session_state.runs_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "run_id": st.column_config.TextColumn("Run ID"),
            "run_no": st.column_config.NumberColumn("Run", step=1),
            "school_type_id": st.column_config.NumberColumn("School", step=1),
            "category": st.column_config.SelectboxColumn("Type", options=["ES", "MS", "HS"], required=True),
            "run_time_min": st.column_config.NumberColumn("Run min", format="%.1f"),
            "start_x": st.column_config.NumberColumn("Start X", format="%.6f"),
            "start_y": st.column_config.NumberColumn("Start Y", format="%.6f"),
            "bell_time_min": st.column_config.NumberColumn("Bell", format="%.1f"),
            "window_min": st.column_config.NumberColumn("Window", format="%.1f"),
        },
    )
    st.session_state.runs_df = edited_df

    add_cols = st.columns([11.7, 1.2], gap="small")
    with add_cols[0]:
        st.write("")
    with add_cols[1]:
        add_row = st.button("Add row", use_container_width=True)

    if add_row:
        next_index = len(st.session_state.runs_df) + 1
        st.session_state.runs_df = pd.concat(
            [
                st.session_state.runs_df,
                pd.DataFrame(
                    [
                        {
                            "run_id": f"Run {next_index}",
                            "run_no": next_index,
                            "school_type_id": 1,
                            "category": "ES",
                            "run_time_min": 20.0,
                            "start_x": 29.0,
                            "start_y": 24.0,
                            "bell_time_min": 190.0,
                            "window_min": 15.0,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        st.rerun()

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

    layout_left, layout_right = st.columns([2.35, 1.2], gap="small")
    with layout_left:
        section_header("Schedule", "Start times selected inside each allowed window.")
        schedule_df = pd.DataFrame(payload["schedule"])[
            ["run_id", "category", "early_bound", "late_bound", "start_time", "ok"]
        ].rename(
            columns={
                "run_id": "Run",
                "category": "Type",
                "early_bound": "Early",
                "late_bound": "Late",
                "start_time": "Start",
                "ok": "OK",
            }
        )
        st.dataframe(schedule_df, use_container_width=True, hide_index=True)
    with layout_right:
        render_routes(payload)

    layout_left, layout_right = st.columns([2.35, 1.2], gap="small")
    with layout_left:
        render_pairings(payload)
    with layout_right:
        render_checks(payload)

    section_header("Deadhead Matrix", "Minutes from a completed run to the next run's school category.")
    matrix_df = pd.DataFrame(payload["deadhead_matrix"], columns=payload["ids"], index=payload["ids"])
    st.dataframe(matrix_df, use_container_width=True)


if __name__ == "__main__":
    main()
