import json
from http.server import BaseHTTPRequestHandler

from school_bus_optimization_based_on_excel_model import RUNS_RAW


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


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        payload = {"runs": [run_to_dict(run) for run in RUNS_RAW]}
        data = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
