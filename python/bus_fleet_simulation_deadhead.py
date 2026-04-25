import pandas as pd
import math

XLS_FILE = "FCPS-Route-Data-for-Model-1.xls"

def classify_school(name: str) -> str:
    name = str(name).upper()
    if "ELEMENTARY" in name:
        return "ES"
    if "MIDDLE" in name:
        return "MS"
    if "HIGH" in name:
        return "HS"
    return "OTHER"

def load_data(xls_path: str):
    schools_base = pd.read_excel(xls_path, sheet_name="Schools Base")
    am_runs = pd.read_excel(xls_path, sheet_name="AM Runs")

    schools_base["Type"] = schools_base["School Name"].apply(classify_school)
    school_type = dict(zip(schools_base["School"], schools_base["Type"]))

    am_runs = am_runs[["Run", "School", "Run Time", "Start X", "Start Y"]].copy()
    am_runs["Type"] = am_runs["School"].map(school_type)

    return schools_base, am_runs

def build_sample(am_runs: pd.DataFrame, schools_base: pd.DataFrame):
    es_runs = am_runs[am_runs["Type"] == "ES"].head(6)
    ms_runs = am_runs[am_runs["Type"] == "MS"].head(2)
    hs_runs = am_runs[am_runs["Type"] == "HS"].head(2)

    sample = pd.concat([es_runs, ms_runs, hs_runs], ignore_index=True)

    school_info = schools_base[["School", "BT (AM)", "Window"]].copy()
    sample = sample.merge(school_info, on="School", how="left")

    sample = sample.reset_index(drop=True)
    sample["RunID"] = sample.index + 1

    return sample

def compute_deadhead_matrix(sample: pd.DataFrame, speed_mph: float = 25.0):
    n = len(sample)
    T = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                T[i][j] = 0.0
            else:
                dx = sample.loc[i, "Start X"] - sample.loc[j, "Start X"]
                dy = sample.loc[i, "Start Y"] - sample.loc[j, "Start Y"]
                dist = math.hypot(dx, dy)
                T[i][j] = 60.0 * dist / speed_mph

    return T

def greedy_linking(sample: pd.DataFrame, T):
    n = len(sample)
    feasible_pairs = []

    for i in range(n):
        BT_i = sample.loc[i, "BT (AM)"]
        for j in range(n):
            if i == j:
                continue
            BT_j = sample.loc[j, "BT (AM)"]
            run_j = sample.loc[j, "Run Time"]

            arrival_j_school = BT_i + T[i][j] + run_j
            if arrival_j_school <= BT_j:
                slack = BT_j - arrival_j_school
                feasible_pairs.append((slack, i, j))

    feasible_pairs.sort(key=lambda x: x[0])

    used_pred = set()
    used_succ = set()
    links = []

    for slack, i, j in feasible_pairs:
        if i in used_pred or j in used_succ:
            continue
        links.append((i, j, slack, T[i][j]))
        used_pred.add(i)
        used_succ.add(j)

    num_buses = n - len(links)

    # ==============================
    # NEW: BUILD ROUTES FROM LINKS
    # ==============================
    succ = {i: None for i in range(n)}
    pred = {i: None for i in range(n)}

    for (i, j, slack, deadhead) in links:
        succ[i] = j
        pred[j] = i

    starts = [i for i in range(n) if pred[i] is None]

    routes = []
    for s in starts:
        route = []
        total_deadhead = 0
        current = s

        while current is not None:
            route.append(current)
            nxt = succ[current]
            if nxt is not None:
                total_deadhead += T[current][nxt]
            current = nxt

        routes.append((route, total_deadhead))

    # ==============================
    # OUTPUT FORMATTING
    # ==============================
    sample_out = sample[
        ["RunID", "Run", "School", "Type", "Run Time", "Start X", "Start Y", "BT (AM)", "Window"]
    ].copy()

    routes_out = pd.DataFrame(
        [
            {
                "Route_ID": idx + 1,
                "Runs_Sequence": " -> ".join(str(sample.loc[r, "RunID"]) for r in route),
                "Schools_Sequence": " -> ".join(str(sample.loc[r, "School"]) for r in route),
                "Num_Runs": len(route),
                "Total_Deadhead_min": round(total_deadhead, 1),
            }
            for idx, (route, total_deadhead) in enumerate(routes)
        ]
    )

    summary = {
        "num_runs": n,
        "num_links": len(links),
        "num_buses": num_buses,
    }

    return summary, sample_out, routes_out


def main():
    schools_base, am_runs = load_data(XLS_FILE)
    sample = build_sample(am_runs, schools_base)
    T = compute_deadhead_matrix(sample, speed_mph=25.0)

    summary, sample_out, routes_out = greedy_linking(sample, T)

    print("=== Sample of Runs ===")
    print(sample_out.to_string(index=False))

    print("\n=== Optimized Routes ===")
    print(routes_out.to_string(index=False))

    print("\n=== Summary ===")
    print(summary)


if __name__ == "__main__":
    main()