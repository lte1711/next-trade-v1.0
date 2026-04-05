const state = {
  payload: null,
  actionResult: null,
  executionLive: false,
};

function el(id) {
  return document.getElementById(id);
}

function fmt(value) {
  if (value === null || value === undefined || value === "") return "-";
  return value;
}

function num(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return Number(value).toFixed(digits);
}

function currency(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return `$${Number(value).toFixed(2)}`;
}

function asJson(value) {
  return JSON.stringify(value ?? {}, null, 2);
}

function setMessage(text, isError = false) {
  const box = el("messageBox");
  box.textContent = text;
  box.className = isError ? "message error" : "message";
}

function currentLiveMode() {
  return el("liveModeToggle").checked;
}

function syncModeUi() {
  state.executionLive = currentLiveMode();
  const modeText = el("liveModeText");
  const live = state.executionLive;
  modeText.textContent = live ? "Live" : "Dry Run";
  modeText.className = live ? "pill live" : "pill dry";
}

function chip(text, tone = "ok") {
  return `<span class="status-chip ${tone}">${text}</span>`;
}

function row(label, value) {
  return `<dt>${label}</dt><dd>${value}</dd>`;
}

function renderMetricCard(items) {
  return `<div class="metric-grid">${items.map((item) => `
    <div class="metric">
      <p class="metric-label">${item.label}</p>
      <p class="metric-value">${item.value}</p>
    </div>
  `).join("")}</div>`;
}

function renderPositionsTable(positions) {
  if (!positions || positions.length === 0) {
    return `<p class="empty-state">No active positions.</p>`;
  }
  return `
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Amount</th>
            <th>Entry</th>
            <th>Mark</th>
            <th>Unrealized</th>
          </tr>
        </thead>
        <tbody>
          ${positions.map((pos) => `
            <tr>
              <td>${fmt(pos.symbol)}</td>
              <td>${fmt(pos.positionAmt)}</td>
              <td>${fmt(pos.entryPrice)}</td>
              <td>${fmt(pos.markPrice)}</td>
              <td>${fmt(pos.unRealizedProfit)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderRiskGateSummary(riskGate) {
  const checks = riskGate.checks || [];
  const failed = checks.filter((item) => !item.ok);
  const chips = [
    chip(riskGate.ok ? "Risk Gate Pass" : "Risk Gate Blocked", riskGate.ok ? "ok" : "danger"),
    chip(`Checks ${checks.length}`, "warn"),
    chip(`Failed ${failed.length}`, failed.length ? "danger" : "ok"),
  ].join("");

  return `
    <div class="status-line">${chips}</div>
    <dl class="key-value-list">
      ${row("Decision", fmt(riskGate.decision_line))}
      ${row("Health Check", fmt(riskGate.recent_health_check?.decision_line || riskGate.recent_health_check?.reason))}
      ${row("Recent Failures", fmt(riskGate.recent_order_failures?.decision_line || riskGate.recent_order_failures?.reason))}
    </dl>
  `;
}

function renderTopRecommendation(paper) {
  const rec = (paper.recommendations || [])[0];
  if (!rec) {
    el("topRecommendation").innerHTML = `
      <div class="status-line">${chip("No Executable Recommendation", "warn")}</div>
      <dl class="key-value-list">
        ${row("Decision", fmt(paper.decision_line))}
        ${row("Blocked Count", fmt((paper.blocked || []).length))}
      </dl>
    `;
    return;
  }

  el("topRecommendation").innerHTML = `
    <div class="status-line">
      ${chip(`Symbol ${fmt(rec.symbol)}`, "ok")}
      ${chip(`Side ${fmt(rec.side)}`, "warn")}
    </div>
    <dl class="key-value-list">
      ${row("Estimated Quantity", fmt(rec.estimated_quantity))}
      ${row("Bullish Score", fmt(rec.bullish_score))}
      ${row("Profit Potential", fmt(rec.profit_potential))}
      ${row("Reason", fmt(rec.reason))}
    </dl>
  `;
}

function renderActionResult() {
  const result = state.actionResult;
  const summary = el("actionResultSummary");
  const raw = el("actionResult");

  if (!result) {
    summary.innerHTML = `<div class="status-line">${chip("No Action Run Yet", "warn")}</div>`;
    raw.textContent = "No action has been run from the dashboard yet.";
    return;
  }

  const ok = result.ok !== false;
  const live = result.live === true || result.dry_run === false;
  const headline = ok ? "Action Completed" : "Action Failed";
  const reason = result.reason || result.result?.reason || result.result?.preview?.reason || "-";

  summary.innerHTML = `
    <div class="status-line">
      ${chip(headline, ok ? "ok" : "danger")}
      ${chip(live ? "Live" : "Dry", live ? "danger" : "ok")}
      ${chip(fmt(result.mode || result.result?.mode || "action"), "warn")}
    </div>
    <dl class="key-value-list">
      ${row("Reason", fmt(reason))}
      ${row("Symbol", fmt(result.symbol || result.result?.symbol || result.recommendation?.symbol))}
      ${row("Status", fmt(result.final_status || result.result?.final_status || result.result?.status))}
    </dl>
  `;
  raw.textContent = asJson(result);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    const error = new Error(payload.reason || payload.error || `Request failed: ${response.status}`);
    error.payload = payload;
    throw error;
  }
  return payload;
}

function render() {
  const payload = state.payload;
  if (!payload) return;
  const snapshot = payload.snapshot;
  const process = payload.autonomous_process || {};
  const account = snapshot.account || {};
  const paper = snapshot.paper_decision || {};
  const op = snapshot.operational_summary || {};
  const lastExec = snapshot.last_execution_report || {};
  const lastAuto = snapshot.last_autonomous_report || {};
  const activePositions = account.positions?.active_positions || [];
  const riskGate = paper.risk_gate || {};

  el("processStatus").innerHTML = `
    <div class="status-line">
      ${chip(process.running ? "Autonomous Running" : "Autonomous Stopped", process.running ? "ok" : "warn")}
      ${chip(process.live ? "Live Process" : "Dry Process", process.live ? "danger" : "ok")}
    </div>
    <dl class="key-value-list">
      ${row("PID", fmt(process.pid))}
      ${row("Mode", fmt(process.mode))}
      ${row("Started", fmt(process.started_at))}
    </dl>
  `;

  el("operationalSummary").innerHTML = renderMetricCard([
    { label: "Profile", value: fmt(op.selected_profile) },
    { label: "Regime", value: fmt(op.market_regime) },
    { label: "Top Symbol", value: fmt(op.top_selected_symbol) },
    { label: "Selected", value: fmt(op.selected_symbol_count) },
  ]) + `
    <dl class="key-value-list">
      ${row("Decision", fmt(op.decision_line))}
    </dl>
  `;

  el("lastExecution").innerHTML = `
    <div class="status-line">
      ${chip(fmt(lastExec.mode || "no execution"), lastExec.executed ? "ok" : "warn")}
      ${chip(lastExec.executed ? "Executed" : "No Execution", lastExec.executed ? "ok" : "warn")}
    </div>
    <dl class="key-value-list">
      ${row("Summary", fmt(lastExec.short_summary || lastExec.alert_summary || lastExec.reason))}
      ${row("Symbol", fmt(lastExec.symbol || lastExec.payload?.symbol))}
    </dl>
  `;

  el("lastAutonomous").innerHTML = renderMetricCard([
    { label: "Entries", value: fmt(lastAuto.entry_count) },
    { label: "Exits", value: fmt(lastAuto.exit_count) },
    { label: "Managed", value: fmt(lastAuto.state_after?.managed_position_count) },
    { label: "Mode", value: fmt(lastAuto.mode) },
  ]) + `
    <dl class="key-value-list">
      ${row("Summary", fmt(lastAuto.decision_line))}
    </dl>
  `;

  el("accountSummary").innerHTML = renderMetricCard([
    { label: "Wallet", value: currency(account.account?.wallet_balance) },
    { label: "Equity", value: currency(account.account?.account_equity) },
    { label: "Unrealized", value: currency(account.account?.unrealized_pnl) },
    { label: "Active Positions", value: fmt(account.positions?.active_position_count) },
  ]);

  el("paperDecision").innerHTML = `
    <div class="status-line">
      ${chip((paper.recommendations || []).length ? "Recommendation Ready" : "No Recommendation", (paper.recommendations || []).length ? "ok" : "warn")}
      ${chip(riskGate.ok ? "Risk Gate Pass" : "Risk Gate Blocked", riskGate.ok ? "ok" : "danger")}
    </div>
    <dl class="key-value-list">
      ${row("Recommendations", fmt((paper.recommendations || []).length))}
      ${row("Blocked Items", fmt((paper.blocked || []).length))}
      ${row("Active Positions", fmt(paper.active_position_count))}
      ${row("Available Slots", fmt(paper.available_slots))}
      ${row("Decision", fmt(paper.decision_line))}
    </dl>
  `;

  renderTopRecommendation(paper);
  renderActionResult();
  el("activePositions").innerHTML = renderPositionsTable(activePositions);
  el("riskGateSummary").innerHTML = renderRiskGateSummary(riskGate);
  el("riskGate").textContent = asJson(riskGate);
}

async function refreshStatus(force = false) {
  try {
    setMessage("Loading status...");
    const url = force ? "/api/status/refresh" : "/api/status";
    const options = force ? { method: "POST", body: "{}" } : {};
    state.payload = await requestJson(url, options);
    render();
    setMessage("Status updated.");
  } catch (error) {
    setMessage(error.message, true);
  }
}

function requireLiveConfirmation(label) {
  if (!state.executionLive) return true;
  return window.confirm(`${label} will send real testnet orders. Continue?`);
}

async function runAction(label, requestFactory, successMessage) {
  try {
    if (!requireLiveConfirmation(label)) {
      setMessage(`${label} cancelled.`);
      return;
    }
    setMessage(`${label} in progress...`);
    const result = await requestFactory();
    state.actionResult = result;
    renderActionResult();
    setMessage(successMessage(result));
    await refreshStatus(true);
  } catch (error) {
    state.actionResult = error.payload || { ok: false, reason: error.message };
    renderActionResult();
    setMessage(error.message, true);
  }
}

async function startAutonomous(live) {
  const label = live ? "Start Live" : "Start Dry";
  await runAction(
    label,
    () => requestJson("/api/autonomous/start", {
      method: "POST",
      body: JSON.stringify({ live, adopt_active_positions: true, interval_seconds: 60 }),
    }),
    (result) => `Autonomous ${live ? "live" : "dry"} process started with pid=${fmt(result.pid)}.`
  );
}

async function stopAutonomous() {
  await runAction(
    "Stop Auto",
    () => requestJson("/api/autonomous/stop", { method: "POST", body: "{}" }),
    (result) => result.stopped ? `Autonomous process ${fmt(result.pid)} stopped.` : fmt(result.reason)
  );
}

async function runHealthCheck() {
  await runAction(
    state.executionLive ? "Health Check Live" : "Health Check Dry",
    () => requestJson("/api/actions/health-check", {
      method: "POST",
      body: JSON.stringify({
        symbol: "BTCUSDT",
        side: "BUY",
        quantity: 0.001,
        live: state.executionLive,
      }),
    }),
    (result) => {
      const openStatus = result.result?.open_result?.final_status || result.result?.preview?.reason || "-";
      const closeStatus = result.result?.close_result?.final_status || "-";
      return `Health check finished. open=${openStatus} close=${closeStatus}`;
    }
  );
}

async function executeTopRecommendation() {
  await runAction(
    state.executionLive ? "Execute Top Live" : "Execute Top Dry",
    () => requestJson("/api/actions/execute-top", {
      method: "POST",
      body: JSON.stringify({ live: state.executionLive }),
    }),
    (result) => `Top recommendation handled with status=${fmt(result.result?.final_status || result.result?.status)}.`
  );
}

async function stopAndCloseAll() {
  await runAction(
    state.executionLive ? "Stop and Close All Live" : "Stop and Close All Dry",
    () => requestJson("/api/actions/stop-and-close-all", {
      method: "POST",
      body: JSON.stringify({ live: state.executionLive }),
    }),
    (result) => `Stop-and-close-all completed. stopped=${fmt(result.stop_result?.stopped)} attempts=${fmt(result.close_result?.close_attempt_count)}.`
  );
}

el("liveModeToggle").addEventListener("change", syncModeUi);
el("refreshBtn").addEventListener("click", () => refreshStatus(true));
el("startDryBtn").addEventListener("click", () => startAutonomous(false));
el("startLiveBtn").addEventListener("click", () => startAutonomous(true));
el("stopBtn").addEventListener("click", stopAutonomous);
el("healthBtn").addEventListener("click", runHealthCheck);
el("execTopBtn").addEventListener("click", executeTopRecommendation);
el("closeAllBtn").addEventListener("click", stopAndCloseAll);

syncModeUi();
renderActionResult();
refreshStatus(false);
setInterval(() => refreshStatus(false), 5000);
