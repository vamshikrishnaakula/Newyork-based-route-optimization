"""
School Bus Optimization Model
==============================
Replicates the Excel model in School_Bus_Optimization_04Apr2026.xlsx

WHAT THE EXCEL DOES
-------------------
Data Sheet:
  For every run i it stores:
    - RunID, run number, school-type, category (ES/MS/HS)
    - Run time Ri (minutes), start coords (Sx_i, Sy_i)
    - Bell time Bi (minutes from midnight), time window Wi
    - School coords (SchoolX, SchoolY) — fixed per category

  It builds a deadhead matrix T[i,j]:
    T[i,j] = sqrt( (Sx_i - SchoolX_j)^2 + (Sy_i - SchoolY_j)^2 ) * 60 / 25
              Euclidean distance, travel speed 25 coord-units/hour -> minutes

Model Sheet:
  Binary assignment Xij (solved by Excel Solver):
    Xij = 1  means after run i, the same bus deadheads to start run j

  Constraints:
    (1) Each run is predecessor of at most one other:   sum_j Xij <= 1
    (2) Each run is successor  of at most one other:    sum_i Xij <= 1
    (3) Feasibility window for run i start time Si:
            Bi - Wi - Ri  <=  Si  <=  Bi - Ri
    (4) Sequencing: if Xij=1 -> Si + Ri + T[i,j] <= Sj  (big-M relaxed)

  Objective: maximise sum Xij  (more pairings -> fewer buses)
             Buses needed = N - sum Xij

This Python script implements the exact same model using scipy.optimize.milp.
"""

import math
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import csc_matrix

# ─────────────────────────────────────────────────────────────────────────────
# 1. INPUT DATA  (matches Data sheet exactly)
# ─────────────────────────────────────────────────────────────────────────────

RUNS_RAW = [
    # (run_id, run_no, school_type_id, category, run_time_min,
    #  start_x, start_y, bell_time_min, window_min, school_x, school_y)
    ("Run 1",  1,  1, "ES",  23, 27.565909,    24.714394,    190, 15, 29.3,  23.9),
    ("Run 2",  2,  1, "ES",  27, 27.705114,    24.850758,    190, 15, 29.3,  23.9),
    ("Run 3",  3,  1, "ES",  11, 28.246780,    24.683902,    190, 15, 29.3,  23.9),
    ("Run 4",  4,  1, "ES",  25, 27.816477,    24.107765,    190, 15, 29.3,  23.9),
    ("Run 5",  5,  1, "ES",  20, 28.631250,    24.531061,    190, 15, 29.3,  23.9),
    ("Run 6",  6,  1, "ES",  17, 29.554356,    24.140530,    190, 15, 29.3,  23.9),
    ("Run 7",  43, 6, "MS",  50, 36.976894,    25.491477,     85, 20, 37.2,  25.6),
    ("Run 8",  44, 6, "MS",  30, 38.445265,    25.811364,     85, 20, 37.2,  25.6),
    ("Run 9",  62, 19,"HS", 111, 26.677083,    27.485985,     75, 20, 38.6,  25.9),
    ("Run 10", 64, 19,"HS",  94, 25.283902,    24.603977,     75, 20, 38.6,  25.9),
]

SCHOOL_COORDS = {"ES": (29.3, 23.9), "MS": (37.2, 25.6), "HS": (38.6, 25.9)}
SPEED   = 25
BIG_M   = 1_000_000.0


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA SHEET CALCULATIONS
# ─────────────────────────────────────────────────────────────────────────────

def deadhead_minutes(sx, sy, cat):
    tx, ty = SCHOOL_COORDS[cat]
    return math.sqrt((sx - tx)**2 + (sy - ty)**2) * 60 / SPEED


def build_data(runs):
    ids = [r[0] for r in runs]
    n   = len(ids)
    R   = np.array([r[4] for r in runs], dtype=float)
    B   = np.array([r[7] for r in runs], dtype=float)
    W   = np.array([r[8] for r in runs], dtype=float)
    Sx  = np.array([r[5] for r in runs], dtype=float)
    Sy  = np.array([r[6] for r in runs], dtype=float)
    cat = [r[3] for r in runs]

    Si_lo = B - W - R
    Si_hi = B - R

    T = np.full((n, n), BIG_M, dtype=float)
    for i in range(n):
        for j in range(n):
            if i != j:
                T[i, j] = deadhead_minutes(Sx[i], Sy[i], cat[j])

    return ids, n, R, B, W, Si_lo, Si_hi, T


# ─────────────────────────────────────────────────────────────────────────────
# 3. OPTIMISATION MODEL
# ─────────────────────────────────────────────────────────────────────────────

def solve(runs=RUNS_RAW):
    ids, n, R, B, W, Si_lo, Si_hi, T = build_data(runs)

    # Variable layout:
    #   [0 .. n*n-1]     : Xij binary
    #   [n*n .. n*n+n-1] : Si continuous
    n2   = n * n
    ntot = n2 + n

    def xv(i, j): return i * n + j
    def sv(i):    return n2 + i

    # Objective: minimise -sum Xij
    c = np.zeros(ntot)
    for i in range(n):
        for j in range(n):
            if i != j:
                c[xv(i, j)] = -1.0

    # Bounds
    lb = np.zeros(ntot)
    ub = np.ones(ntot)
    for i in range(n):
        ub[xv(i, i)] = 0.0          # no self-link
        lb[sv(i)]    = Si_lo[i]
        ub[sv(i)]    = Si_hi[i]
    bounds = Bounds(lb=lb, ub=ub)

    # Integrality: Xij binary
    integrality = np.zeros(ntot)
    for i in range(n):
        for j in range(n):
            integrality[xv(i, j)] = 1

    # Build constraint matrix
    row_list, col_list, dat_list, lo_list, hi_list = [], [], [], [], []

    def add_row(cols, coefs, lo_val, hi_val):
        ridx = len(lo_list)
        for ci, cf in zip(cols, coefs):
            row_list.append(ridx)
            col_list.append(ci)
            dat_list.append(cf)
        lo_list.append(lo_val)
        hi_list.append(hi_val)

    # C1: sum_j Xij <= 1
    for i in range(n):
        add_row([xv(i, j) for j in range(n) if j != i], [1.0]*(n-1), -np.inf, 1.0)

    # C2: sum_i Xij <= 1
    for j in range(n):
        add_row([xv(i, j) for i in range(n) if i != j], [1.0]*(n-1), -np.inf, 1.0)

    # C4: Si - Sj + BIG_M*Xij <= BIG_M - Ri - T[i,j]
    for i in range(n):
        for j in range(n):
            if i != j:
                add_row([sv(i), sv(j), xv(i, j)],
                        [1.0,  -1.0,  BIG_M],
                        -np.inf,
                        BIG_M - R[i] - T[i, j])

    nrows = len(lo_list)
    A = csc_matrix((dat_list, (row_list, col_list)), shape=(nrows, ntot))
    constraints = LinearConstraint(A, np.array(lo_list), np.array(hi_list))

    result = milp(c, constraints=constraints, integrality=integrality, bounds=bounds)
    return result, ids, n, R, B, W, Si_lo, Si_hi, T, n2


# ─────────────────────────────────────────────────────────────────────────────
# 4. RESULTS
# ─────────────────────────────────────────────────────────────────────────────

def print_results(runs=RUNS_RAW):
    result, ids, n, R, B, W, Si_lo, Si_hi, T, n2 = solve(runs)

    def xv(i, j): return i * n + j
    def sv(i):    return n2 + i

    print(f"\n{'='*65}")
    print("  SCHOOL BUS OPTIMISATION RESULTS")
    print(f"{'='*65}")
    print(f"  Solver status  : {result.message}")

    if result.x is None:
        print("  No solution found.")
        return None, None

    x = result.x
    pairings = [(ids[i], ids[j])
                for i in range(n) for j in range(n)
                if i != j and x[xv(i, j)] > 0.5]
    buses_needed = n - len(pairings)

    print(f"  Total runs     : {n}")
    print(f"  Pairings found : {len(pairings)}")
    print(f"  Buses needed   : {buses_needed}")

    print(f"\n{'─'*65}")
    print("  RUN SCHEDULE")
    print(f"{'─'*65}")
    print(f"  {'Run':<8} {'Ri':>5} {'Bi':>5} {'Wi':>4} {'EarlyBound':>11} {'LateBound':>10} {'StartTime*':>11}  OK?")
    for i, rid in enumerate(ids):
        si = x[sv(i)]
        ok = "OK" if Si_lo[i] - 0.5 <= si <= Si_hi[i] + 0.5 else "FAIL"
        print(f"  {rid:<8} {R[i]:>5.0f} {B[i]:>5.0f} {W[i]:>4.0f} "
              f"{Si_lo[i]:>11.1f} {Si_hi[i]:>10.1f} {si:>11.1f}  {ok}")

    print(f"\n{'─'*65}")
    print("  BUS PAIRINGS (Run i -> Run j, deadhead T[i,j] minutes)")
    print(f"{'─'*65}")
    if pairings:
        for (ri, rj) in pairings:
            ii, ij = ids.index(ri), ids.index(rj)
            print(f"  {ri}  ->  {rj}   (deadhead = {T[ii, ij]:.2f} min)")
    else:
        print("  No pairings found — each run needs its own bus.")

    print(f"\n{'─'*65}")
    print("  DEADHEAD MATRIX T[i,j] (minutes)")
    print(f"{'─'*65}")
    print(f"  {'':10}" + "".join(f"{ids[j][-2:]:>8}" for j in range(n)))
    for i in range(n):
        row = f"  {ids[i]:<10}"
        for j in range(n):
            row += f"{'---':>8}" if T[i, j] >= BIG_M else f"{T[i, j]:>8.2f}"
        print(row)

    print()
    return buses_needed, pairings


if __name__ == "__main__":
    print_results(RUNS_RAW)
