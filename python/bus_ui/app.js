const runsBody = document.querySelector("#runsBody");
const rowTemplate = document.querySelector("#runRowTemplate");
const solveButton = document.querySelector("#solveButton");
const resetButton = document.querySelector("#resetButton");
const addRunButton = document.querySelector("#addRunButton");
const totalRuns = document.querySelector("#totalRuns");
const pairingsFound = document.querySelector("#pairingsFound");
const busesNeeded = document.querySelector("#busesNeeded");
const solverStatus = document.querySelector("#solverStatus");
const scheduleBody = document.querySelector("#scheduleBody");
const pairingsList = document.querySelector("#pairingsList");
const routesList = document.querySelector("#routesList");
const checksList = document.querySelector("#checksList");
const matrixTable = document.querySelector("#matrixTable");

let defaultRuns = [];

function setStatus(message) {
  solverStatus.textContent = message;
}

function cloneRun(run, index) {
  return {
    run_id: run?.run_id ?? `Run ${index + 1}`,
    run_no: run?.run_no ?? index + 1,
    school_type_id: run?.school_type_id ?? 1,
    category: run?.category ?? "ES",
    run_time_min: run?.run_time_min ?? 20,
    start_x: run?.start_x ?? 29,
    start_y: run?.start_y ?? 24,
    bell_time_min: run?.bell_time_min ?? 190,
    window_min: run?.window_min ?? 15,
  };
}

function renderRuns(runs) {
  runsBody.replaceChildren();
  runs.map(cloneRun).forEach((run) => {
    const row = rowTemplate.content.firstElementChild.cloneNode(true);
    Object.entries(run).forEach(([key, value]) => {
      const field = row.querySelector(`[name="${key}"]`);
      if (field) {
        field.value = value;
      }
    });
    row.querySelector(".remove-row").addEventListener("click", () => {
      row.remove();
      totalRuns.textContent = String(readRuns().length);
    });
    runsBody.append(row);
  });
  totalRuns.textContent = String(runs.length);
}

function readNumber(row, name) {
  const value = row.querySelector(`[name="${name}"]`).value;
  const number = Number(value);
  if (!Number.isFinite(number)) {
    throw new Error(`${name} must be numeric.`);
  }
  return number;
}

function readRuns() {
  return [...runsBody.querySelectorAll("tr")].map((row, index) => ({
    run_id: row.querySelector('[name="run_id"]').value.trim() || `Run ${index + 1}`,
    run_no: readNumber(row, "run_no"),
    school_type_id: readNumber(row, "school_type_id"),
    category: row.querySelector('[name="category"]').value,
    run_time_min: readNumber(row, "run_time_min"),
    start_x: readNumber(row, "start_x"),
    start_y: readNumber(row, "start_y"),
    bell_time_min: readNumber(row, "bell_time_min"),
    window_min: readNumber(row, "window_min"),
  }));
}

function formatNumber(value, digits = 1) {
  return Number(value).toFixed(digits);
}

function renderSchedule(schedule) {
  scheduleBody.replaceChildren();
  schedule.forEach((run) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${run.run_id}</td>
      <td>${run.category}</td>
      <td>${formatNumber(run.early_bound)}</td>
      <td>${formatNumber(run.late_bound)}</td>
      <td>${formatNumber(run.start_time)}</td>
      <td><span class="${run.ok ? "ok-pill" : "fail-pill"}">${run.ok ? "OK" : "Fail"}</span></td>
    `;
    scheduleBody.append(row);
  });
}

function renderPairings(pairings) {
  pairingsList.replaceChildren();
  if (!pairings.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No pairings found. Each run needs its own bus.";
    pairingsList.append(empty);
    return;
  }

  pairings.forEach((pairing) => {
    const item = document.createElement("div");
    item.className = "pairing-item";
    item.innerHTML = `
      <div>
        <div class="pairing-route">${pairing.from} -> ${pairing.to}</div>
        <div class="pairing-meta">Deadhead ${formatNumber(pairing.deadhead_min, 2)} min</div>
      </div>
      <span class="ok-pill">Linked</span>
    `;
    pairingsList.append(item);
  });
}

function renderRoutes(routes) {
  routesList.replaceChildren();
  routes.forEach((route) => {
    const item = document.createElement("div");
    item.className = "route-item";
    item.innerHTML = `
      <div>
        <div class="route-name">Bus ${route.bus}</div>
        <div class="route-meta">${route.runs.join(" -> ")}</div>
      </div>
      <span class="ok-pill">${route.run_count} run${route.run_count === 1 ? "" : "s"}</span>
    `;
    routesList.append(item);
  });
}

function addCheck(label, ok, detail = "") {
  const item = document.createElement("div");
  item.className = "check-item";
  item.innerHTML = `
    <div>
      <div class="check-name">${label}</div>
      <div class="check-meta">${detail}</div>
    </div>
    <span class="${ok ? "ok-pill" : "fail-pill"}">${ok ? "OK" : "Fail"}</span>
  `;
  checksList.append(item);
}

function renderChecks(checks) {
  checksList.replaceChildren();
  addCheck("One successor per run", checks.one_successor_per_run, "No run starts two later runs.");
  addCheck("One predecessor per run", checks.one_predecessor_per_run, "No run is assigned to two previous runs.");
  addCheck("Start windows", checks.all_start_times_in_windows, "Every start time is inside its early and late bound.");
  addCheck("Sequencing", checks.all_pairings_sequence, "Each paired bus reaches the next run before its start time.");
}

function renderMatrix(matrix, ids) {
  const head = `
    <thead>
      <tr>
        <th>From / To</th>
        ${ids.map((id) => `<th>${id}</th>`).join("")}
      </tr>
    </thead>
  `;
  const body = matrix.map((row, index) => `
    <tr>
      <th>${ids[index]}</th>
      ${row.map((value) => `<td>${value === null ? "---" : formatNumber(value, 2)}</td>`).join("")}
    </tr>
  `).join("");
  matrixTable.innerHTML = `${head}<tbody>${body}</tbody>`;
}

function renderResults(data) {
  totalRuns.textContent = String(data.total_runs);
  pairingsFound.textContent = String(data.pairings_found);
  busesNeeded.textContent = String(data.buses_needed);
  setStatus(data.status);
  renderSchedule(data.schedule);
  renderPairings(data.pairings);
  renderRoutes(data.routes);
  renderChecks(data.checks);
  renderMatrix(data.deadhead_matrix, data.ids);
}

async function optimize() {
  try {
    const runs = readRuns();
    if (runs.length < 2) {
      throw new Error("Add at least two runs before optimizing.");
    }

    solveButton.disabled = true;
    setStatus("Solving...");
    const response = await fetch("/api/solve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ runs }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Optimization failed.");
    }
    renderResults(data);
  } catch (error) {
    setStatus(error.message);
  } finally {
    solveButton.disabled = false;
  }
}

async function loadDefaults() {
  setStatus("Loading sample...");
  const response = await fetch("/api/default-data");
  const data = await response.json();
  defaultRuns = data.runs;
  renderRuns(defaultRuns);
  await optimize();
}

solveButton.addEventListener("click", optimize);
resetButton.addEventListener("click", () => {
  renderRuns(defaultRuns);
  optimize();
});
addRunButton.addEventListener("click", () => {
  const runs = readRuns();
  runs.push(cloneRun(null, runs.length));
  renderRuns(runs);
});

loadDefaults();
