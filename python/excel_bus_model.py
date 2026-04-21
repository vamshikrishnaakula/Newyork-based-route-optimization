import math

import pandas as pd


XLS_FILE = "FCPS-Route-Data-for-Model-1.xls"
DEADHEAD_SPEED_MPH = 25

# The spreadsheet model shown in the screenshots uses these three schools as
# the representative ES/MS/HS destinations for the 10-run sample.
SCHOOL_TYPES = {
    "ES": 1,
    "MS": 6,
    "HS": 19,
}


def load_sample(xls_file: str = XLS_FILE) -> tuple[pd.DataFrame, pd.DataFrame]:
    schools = pd.read_excel(xls_file, sheet_name="Schools Base")
    runs = pd.read_excel(xls_file, sheet_name="AM Runs")

    sample_parts = [
        runs[runs["School"] == SCHOOL_TYPES["ES"]].head(6),
        runs[runs["School"] == SCHOOL_TYPES["MS"]].head(2),
        runs[runs["School"] == SCHOOL_TYPES["HS"]].head(2),
    ]
    sample = pd.concat(sample_parts, ignore_index=True)
    sample = sample[["Run", "School", "Run Time", "Start X", "Start Y"]].copy()

    school_info = schools[["School", "BT (AM)", "Window", "School X", "School Y"]]
    sample = sample.merge(school_info[["School", "BT (AM)", "Window"]], on="School", how="left")

    type_by_school = {school: school_type for school_type, school in SCHOOL_TYPES.items()}
    sample.insert(0, "RunID", [f"Run {i}" for i in range(1, len(sample) + 1)])
    sample.insert(2, "School Type category", sample["School"].map(type_by_school))

    return sample, schools


def representative_school_coordinates(schools: pd.DataFrame) -> dict[str, tuple[float, float]]:
    coords = {}
    for school_type, school_id in SCHOOL_TYPES.items():
        row = schools.loc[schools["School"] == school_id].iloc[0]
        # Match the visible Excel model, where school coordinates are rounded to
        # one decimal before the distance formulas are applied.
        coords[school_type] = (round(float(row["School X"]), 1), round(float(row["School Y"]), 1))
    return coords


def build_input_table(sample: pd.DataFrame, coords: dict[str, tuple[float, float]]) -> pd.DataFrame:
    school_x = sample["School Type category"].map(lambda school_type: coords[school_type][0])
    school_y = sample["School Type category"].map(lambda school_type: coords[school_type][1])

    return pd.DataFrame(
        {
            "RunID": sample["RunID"],
            "Run": sample["Run"],
            "School": sample["School"],
            "School Type category": sample["School Type category"],
            "Run Time": sample["Run Time"],
            "Start X": sample["Start X"],
            "Start Y": sample["Start Y"],
            "BT (AM)": sample["BT (AM)"],
            "Window": sample["Window"],
            "School X": school_x,
            "School Y": school_y,
        }
    )


def build_distance_blocks(sample: pd.DataFrame, coords: dict[str, tuple[float, float]]):
    runs = sample["RunID"]

    x_diff_sq = pd.DataFrame({"Runs": runs, "Schools": sample["Start X"]})
    y_diff_sq = pd.DataFrame({"Runs": runs, "Schools": sample["Start Y"]})
    distance = pd.DataFrame({"Runs": runs})
    minutes = pd.DataFrame({"Runs": runs})

    for school_type, (school_x, school_y) in coords.items():
        dx_sq = (sample["Start X"] - school_x) ** 2
        dy_sq = (sample["Start Y"] - school_y) ** 2
        dist = (dx_sq + dy_sq).map(math.sqrt)

        x_diff_sq[school_type] = dx_sq
        y_diff_sq[school_type] = dy_sq
        distance[school_type] = dist
        minutes[school_type] = 60 * dist / DEADHEAD_SPEED_MPH

    return x_diff_sq, y_diff_sq, distance, minutes


def deadhead_to_next_run(next_run: pd.Series, previous_school_type: str, coords: dict[str, tuple[float, float]]) -> float:
    school_x, school_y = coords[previous_school_type]
    dx = float(next_run["Start X"]) - school_x
    dy = float(next_run["Start Y"]) - school_y
    distance = math.sqrt(dx * dx + dy * dy)
    return 60 * distance / DEADHEAD_SPEED_MPH


def build_feasible_links(sample: pd.DataFrame, coords: dict[str, tuple[float, float]]):
    feasible_pairs = []
    feasible_matrix = pd.DataFrame(0, index=sample["RunID"], columns=sample["RunID"])
    slack_matrix = pd.DataFrame("", index=sample["RunID"], columns=sample["RunID"])

    for i, previous_run in sample.iterrows():
        previous_type = previous_run["School Type category"]
        for j, next_run in sample.iterrows():
            if i == j:
                continue

            deadhead_min = deadhead_to_next_run(next_run, previous_type, coords)
            arrival_at_next_school = (
                float(previous_run["BT (AM)"])
                + deadhead_min
                + float(next_run["Run Time"])
            )
            slack = float(next_run["BT (AM)"]) - arrival_at_next_school

            if slack >= 0:
                from_run = previous_run["RunID"]
                to_run = next_run["RunID"]
                feasible_matrix.loc[from_run, to_run] = 1
                slack_matrix.loc[from_run, to_run] = f"{slack:.4f}"
                feasible_pairs.append(
                    {
                        "From": from_run,
                        "To": to_run,
                        "From_Type": previous_type,
                        "To_Type": next_run["School Type category"],
                        "Deadhead_min": deadhead_min,
                        "Slack_min": slack,
                        "from_index": i,
                        "to_index": j,
                    }
                )

    return feasible_pairs, feasible_matrix, slack_matrix


def select_routes(sample: pd.DataFrame, feasible_pairs: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected = []
    used_successor = set()
    used_predecessor = set()

    for pair in sorted(feasible_pairs, key=lambda item: item["Slack_min"]):
        if pair["from_index"] in used_successor:
            continue
        if pair["to_index"] in used_predecessor:
            continue
        selected.append(pair)
        used_successor.add(pair["from_index"])
        used_predecessor.add(pair["to_index"])

    links = pd.DataFrame(
        [
            {
                "From_RunID": pair["From"],
                "To_RunID": pair["To"],
                "From_Type": pair["From_Type"],
                "To_Type": pair["To_Type"],
                "Deadhead_min": round(pair["Deadhead_min"], 4),
                "Slack_min": round(pair["Slack_min"], 4),
            }
            for pair in selected
        ]
    )

    successor = {i: None for i in sample.index}
    predecessor = {i: None for i in sample.index}
    for pair in selected:
        successor[pair["from_index"]] = pair["to_index"]
        predecessor[pair["to_index"]] = pair["from_index"]

    routes = []
    for start in [i for i in sample.index if predecessor[i] is None]:
        sequence = []
        current = start
        while current is not None:
            sequence.append(current)
            current = successor[current]

        routes.append(
            {
                "Bus": len(routes) + 1,
                "Runs_Sequence": " -> ".join(sample.loc[i, "RunID"] for i in sequence),
                "Original_Runs": " -> ".join(str(sample.loc[i, "Run"]) for i in sequence),
                "Schools_Sequence": " -> ".join(str(sample.loc[i, "School"]) for i in sequence),
                "Types_Sequence": " -> ".join(sample.loc[i, "School Type category"] for i in sequence),
                "Num_Runs": len(sequence),
            }
        )

    return links, pd.DataFrame(routes)


def print_block(title: str, df: pd.DataFrame, decimals: int | None = None) -> None:
    print(f"\n=== {title} ===")
    if decimals is None:
        print(df.to_string(index=False))
    else:
        print(df.round(decimals).to_string(index=False))


def main() -> None:
    sample, schools = load_sample()
    coords = representative_school_coordinates(schools)

    input_table = build_input_table(sample, coords)
    x_diff_sq, y_diff_sq, distance, minutes = build_distance_blocks(sample, coords)
    feasible_pairs, feasible_matrix, slack_matrix = build_feasible_links(sample, coords)
    selected_links, routes = select_routes(sample, feasible_pairs)

    print_block("Input Table", input_table, 4)
    print_block("School X Difference Squared", x_diff_sq, 4)
    print_block("School Y Difference Squared", y_diff_sq, 4)
    print_block("Distance", distance, 4)
    print_block("Distance In Minutes", minutes, 4)

    print("\n=== Feasible Link Matrix (1 = bus can do row run, then column run) ===")
    print(feasible_matrix.to_string())

    print("\n=== Feasible Link Slack Matrix (minutes) ===")
    print(slack_matrix.to_string())

    print_block("Selected Links", selected_links)
    print_block("Bus Routes", routes)

    print("\n=== Summary ===")
    print(f"Number of runs: {len(sample)}")
    print(f"Number of selected links: {len(selected_links)}")
    print(f"Number of buses required: {len(sample) - len(selected_links)}")


if __name__ == "__main__":
    main()
