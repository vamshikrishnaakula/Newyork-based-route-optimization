import pandas as pd
import math

XLS_FILE = "FCPS-Route-Data-for-Model-1.xls"

def classify_school(name: str) -> str:
    """
    Classify school by its name into ES (elementary), MS (middle), HS (high), OTHER.
    """
    name = str(name).upper()
    if "ELEMENTARY" in name:
        return "ES"
    if "MIDDLE" in name:
        return "MS"
    if "HIGH" in name:
        return "HS"
    return "OTHER"

def load_data(xls_path: str):
    #base school info and AM runs
    schools_base = pd.read_excel(xls_path, sheet_name="Schools Base")
    am_runs = pd.read_excel(xls_path, sheet_name="AM Runs")

    # Classify schools
    schools_base["Type"] = schools_base["School Name"].apply(classify_school)

    # Map school index -> type
    school_type = dict(zip(schools_base["School"], schools_base["Type"]))

    # Keep only relevant columns from AM runs
    am_runs = am_runs[["Run", "School", "Run Time", "Start X", "Start Y"]].copy()
    am_runs["Type"] = am_runs["School"].map(school_type)

    return schools_base, am_runs

def build_sample(am_runs: pd.DataFrame, schools_base: pd.DataFrame):
    """
    Build a sample of 10 runs:
      - 6 elementary (ES)
      - 2 middle (MS)
      - 2 high (HS)
    Deterministic: use first occurrences.
    """
    es_runs = am_runs[am_runs["Type"] == "ES"].head(6)
    ms_runs = am_runs[am_runs["Type"] == "MS"].head(2)
    hs_runs = am_runs[am_runs["Type"] == "HS"].head(2)

    sample = pd.concat([es_runs, ms_runs, hs_runs], ignore_index=True)

    # Attach bell time and window from Schools Base
    school_info = schools_base[["School", "BT (AM)", "Window"]].copy()
    sample = sample.merge(school_info, on="School", how="left")

    # Renumber runs 1..10 for this sample
    sample = sample.reset_index(drop=True)
    sample["RunID"] = sample.index + 1

    return sample

def compute_deadhead_matrix(sample: pd.DataFrame, speed_mph: float = 25.0):
    """
    Compute deadhead time matrix between starts of runs in minutes.
    Distances in miles, time = 60 * dist / speed.
    """
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
    """
    Greedy linking heuristic:
      - Assume run i arrives at its school exactly at BT_i (latest allowed).
      - After finishing i, bus deadheads to j's start (T_ij minutes).
      - Then run j takes RunTime_j; arrival at j's school must be <= BT_j.
      - Build feasible (i, j) pairs with slack, sort by smallest slack,
        and greedily add links with at most one predecessor and one successor per run.
    """
    n = len(sample)
    feasible_pairs = []

    for i in range(n):
        BT_i = sample.loc[i, "BT (AM)"]
        for j in range(n):
            if i == j:
                continue
            BT_j = sample.loc[j, "BT (AM)"]
            run_j = sample.loc[j, "Run Time"]

            # Arrival at j's school if we do j after i
            arrival_j_school = BT_i + T[i][j] + run_j
            if arrival_j_school <= BT_j:
                slack = BT_j - arrival_j_school
                feasible_pairs.append((slack, i, j))

    # Sort by tightest slack first
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

    # Build nice DataFrames for inspection
    sample_out = sample[
        ["RunID", "Run", "School", "Type", "Run Time", "Start X", "Start Y", "BT (AM)", "Window"]
    ].copy()

    links_out = pd.DataFrame(
        [
            {
                "From_RunID": sample.loc[i, "RunID"],
                "To_RunID": sample.loc[j, "RunID"],
                "From_School": sample.loc[i, "School"],
                "To_School": sample.loc[j, "School"],
                "Deadhead_min": round(T[i][j], 1),
                "Slack_min": round(slack, 1),
            }
            for (i, j, slack, _) in links
        ]
    )

    summary = {
        "num_runs": n,
        "num_links": len(links),
        "num_buses": num_buses,
    }

    return summary, sample_out, links_out

def main():
    schools_base, am_runs = load_data(XLS_FILE)
    sample = build_sample(am_runs, schools_base)
    T = compute_deadhead_matrix(sample, speed_mph=25.0)
    summary, sample_out, links_out = greedy_linking(sample, T)

    print("=== Sample of 10 Runs (6 ES, 2 MS, 2 HS) ===")
    print(sample_out.to_string(index=False))
    print("\n=== Greedy Links ===")
    print(links_out.to_string(index=False))
    print("\n=== Summary ===")
    print(summary)

if __name__ == "__main__":
    main()
