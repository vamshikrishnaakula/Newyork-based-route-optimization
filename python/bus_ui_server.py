import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from school_bus_optimization_based_on_excel_model import BIG_M, RUNS_RAW, solve


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "bus_ui"


def run_to_dict(run):
    return {
        "run_id": run[0],
        "run_no": run[1],
        "school_type_id": run[2],
        "category": run[3],
        "run_time_min": run[4],
        "start_x": run[5],
        "start_y": run[6],
        "bell_time_min": run[7],
        "window_min": run[8],
    }


def dict_to_run(item, index):
    category = str(item.get("category", "ES")).upper()
    if category not in {"ES", "MS", "HS"}:
        raise ValueError(f"Run {index + 1}: category must be ES, MS, or HS.")

    return (
        str(item.get("run_id") or f"Run {index + 1}"),
        int(float(item.get("run_no", index + 1))),
        int(float(item.get("school_type_id", 1))),
        category,
        float(item["run_time_min"]),
        float(item["start_x"]),
        float(item["start_y"]),
        float(item["bell_time_min"]),
        float(item["window_min"]),
        0.0,
        0.0,
    )


def solve_payload(runs):
    result, ids, n, run_times, bell_times, windows, early, late, deadhead, n2 = solve(runs)

    if result.x is None:
        return {
            "status": result.message,
            "total_runs": n,
            "pairings_found": 0,
            "buses_needed": n,
            "ids": ids,
            "schedule": [],
            "pairings": [],
            "deadhead_matrix": [],
        }

    def xv(i, j):
        return i * n + j

    def sv(i):
        return n2 + i

    x = result.x
    pairings = []
    successor = {}
    predecessor = {}
    for i in range(n):
        for j in range(n):
            if i != j and x[xv(i, j)] > 0.5:
                successor[i] = j
                predecessor[j] = i
                pairings.append(
                    {
                        "from": ids[i],
                        "to": ids[j],
                        "deadhead_min": round(float(deadhead[i, j]), 4),
                    }
                )

    schedule = []
    for i, run_id in enumerate(ids):
        start_time = float(x[sv(i)])
        schedule.append(
            {
                "run_id": run_id,
                "category": runs[i][3],
                "run_time": float(run_times[i]),
                "bell_time": float(bell_times[i]),
                "window": float(windows[i]),
                "early_bound": float(early[i]),
                "late_bound": float(late[i]),
                "start_time": start_time,
                "ok": bool(early[i] - 0.5 <= start_time <= late[i] + 0.5),
                }
            )

    routes = []
    for start in [i for i in range(n) if i not in predecessor]:
        route = []
        current = start
        while current is not None:
            route.append(ids[current])
            current = successor.get(current)
        routes.append({"bus": len(routes) + 1, "runs": route, "run_count": len(route)})

    sequencing_ok = True
    sequencing_checks = []
    for from_index, to_index in successor.items():
        lhs = float(x[sv(from_index)] + run_times[from_index] + deadhead[from_index, to_index])
        rhs = float(x[sv(to_index)])
        ok = lhs <= rhs + 0.0001
        sequencing_ok = sequencing_ok and ok
        sequencing_checks.append(
            {
                "from": ids[from_index],
                "to": ids[to_index],
                "arrival_ready_time": round(lhs, 4),
                "next_start_time": round(rhs, 4),
                "ok": ok,
            }
        )

    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(None if deadhead[i, j] >= BIG_M else round(float(deadhead[i, j]), 4))
        matrix.append(row)

    return {
        "status": result.message,
        "total_runs": n,
        "pairings_found": len(pairings),
        "buses_needed": n - len(pairings),
        "ids": ids,
        "schedule": schedule,
        "pairings": pairings,
        "routes": routes,
        "checks": {
            "one_successor_per_run": len(successor) == len(set(successor.keys())),
            "one_predecessor_per_run": len(predecessor) == len(set(predecessor.keys())),
            "all_start_times_in_windows": all(item["ok"] for item in schedule),
            "all_pairings_sequence": sequencing_ok,
            "sequencing": sequencing_checks,
        },
        "deadhead_matrix": matrix,
    }


class BusUIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def send_json(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/default-data":
            self.send_json(200, {"runs": [run_to_dict(run) for run in RUNS_RAW]})
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/solve":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            run_items = payload.get("runs")
            if not isinstance(run_items, list) or len(run_items) < 2:
                raise ValueError("Send at least two runs.")
            runs = [dict_to_run(item, index) for index, item in enumerate(run_items)]
            self.send_json(200, solve_payload(runs))
        except Exception as exc:
            self.send_json(400, {"error": str(exc)})


def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), BusUIHandler)
    print(f"School Bus Optimizer UI running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
