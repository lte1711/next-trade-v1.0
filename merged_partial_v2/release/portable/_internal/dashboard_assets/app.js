const state = {
  payload: null,
  actionResult: null,
  refreshInFlight: false,
};

function el(id) {
  return document.getElementById(id);
}

function setText(id, value) {
  const node = el(id);
  if (node) node.textContent = value ?? "";
}

function setHtml(id, value) {
  const node = el(id);
  if (node) node.innerHTML = value ?? "";
}

function fmt(value) {
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
}

function num(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function money(value) {
  const parsed = num(value);
  return parsed === null ? "-" : `$${parsed.toFixed(2)}`;
}

function pct(value) {
  const parsed = num(value);
  return parsed === null ? "-" : `${parsed.toFixed(2)}%`;
}

function shortTs(value) {
  if (!value) return "-";
  return String(value).replace("T", " ").replace("+00:00", " UTC");
}

function json(value) {
  try {
    return JSON.stringify(value ?? {}, null, 2);
  } catch {
    return "{}";
  }
}

function average(values) {
  const nums = values.map(num).filter((value) => value !== null);
  if (!nums.length) return null;
  return nums.reduce((sum, value) => sum + value, 0) / nums.length;
}

function chip(label, tone = "warn") {
  return `<span class="pill ${tone}">${fmt(label)}</span>`;
}

function row(label, value) {
  return `<div class="kv-row"><dt>${fmt(label)}</dt><dd>${fmt(value)}</dd></div>`;
}

function metricGrid(items) {
  return `<div class="metric-grid">${items.map((item) => `
    <article class="metric-card">
      <p class="metric-label">${fmt(item.label)}</p>
      <p class="metric-value">${fmt(item.value)}</p>
    </article>
  `).join("")}</div>`;
}

function modeLabel(value) {
  const map = {
    autonomous_loop: "자동 반복",
    autonomous_cycle: "자동매매 사이클",
    execute_top_recommendation: "자동 추천 실행",
    stop_and_close_all: "전체 정리",
    health_check_order: "헬스체크",
    no_execution_report: "실행 이력 없음",
    action: "수동 실행",
  };
  return map[value] || fmt(value);
}

function reasonLabel(value) {
  const map = {
    no_process_record: "자동매매 기록이 없습니다.",
    autonomous_process_not_running: "자동매매가 실행 중이 아닙니다.",
    no_recommendation: "실행 가능한 추천이 없습니다.",
    no_autonomous_report: "자동매매 리포트가 없습니다.",
    no_health_check_records: "헬스체크 기록이 없습니다.",
    manual_execute_disabled_use_autonomous: "추천 실행은 자동매매 사이클에서 자동 처리됩니다.",
  };
  return map[value] || fmt(value);
}

function orderStatusLabel(value) {
  if (!value) return "-";
  const map = {
    FILLED: "체결 완료",
    NEW: "접수",
    COMPLETED: "완료",
    FAILED: "실패",
    CANCELED: "취소",
  };
  return map[value] || fmt(value);
}

function message(text, isError = false) {
  setHtml("messageBox", `<span class="${isError ? "text-danger" : ""}">${fmt(text)}</span>`);
}

function enrichPositions(snapshot) {
  const activePositions = snapshot.account?.positions?.active_positions || [];
  const selected = snapshot.market?.selected_symbols || [];
  const bySymbol = new Map(selected.map((item) => [item.symbol, item]));
  return activePositions.map((position) => {
    const market = bySymbol.get(position.symbol) || {};
    return {
      symbol: position.symbol,
      quantity: num(position.positionAmt),
      entryPrice: num(position.entryPrice),
      markPrice: num(position.markPrice),
      pnl: num(position.unRealizedProfit),
      riseProbability: num(market.profit_potential),
      actualChangeRate: market.change_percent,
    };
  });
}

function positionsTable(positions) {
  if (!positions.length) return "<p>활성 포지션이 없습니다.</p>";
  return `
    <table class="data-table">
      <thead>
        <tr>
          <th>종목</th>
          <th>수량</th>
          <th>진입가</th>
          <th>현재가</th>
          <th>미실현 손익</th>
          <th>상승률 점수</th>
        </tr>
      </thead>
      <tbody>
        ${positions.map((item) => `
          <tr>
            <td>${fmt(item.symbol)}</td>
            <td>${fmt(item.quantity)}</td>
            <td>${fmt(item.entryPrice)}</td>
            <td>${fmt(item.markPrice)}</td>
            <td>${money(item.pnl)}</td>
            <td>${pct(item.riseProbability)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function riskGateSummary(riskGate) {
  return `
    <div class="status-line">
      ${chip(riskGate.ok ? "리스크 게이트 통과" : "리스크 게이트 차단", riskGate.ok ? "ok" : "danger")}
      ${chip((riskGate.reasons || []).length ? `${riskGate.reasons.length}건 사유` : "차단 사유 없음", (riskGate.reasons || []).length ? "warn" : "ok")}
    </div>
    <dl class="key-value-list">
      ${row("판정", fmt(riskGate.decision_line))}
      ${row("최근 실패 수", fmt(riskGate.recent_order_failures?.failure_count))}
      ${row("시장 상태", fmt(riskGate.market_regime))}
    </dl>
  `;
}

function renderTopRecommendation(paper) {
  const rec = (paper.recommendations || [])[0];
  if (!rec) {
    setHtml("topRecommendation", "<p>현재 자동 진입 후보가 없습니다.</p>");
    return;
  }
  setHtml("topRecommendation", `
    <div class="status-line">
      ${chip(rec.symbol, "ok")}
      ${chip("자동 실행 후보", "warn")}
    </div>
    <dl class="key-value-list">
      ${row("종목", rec.symbol)}
      ${row("방향", rec.side)}
      ${row("예상 수량", rec.estimated_quantity)}
      ${row("배정 금액", money(rec.allocation))}
      ${row("상승률", pct(rec.profit_potential))}
      ${row("판정", fmt(rec.reason))}
    </dl>
  `);
}

function renderActionResult() {
  const result = state.actionResult || {};
  const ok = result.ok !== false;
  const reason = result.reason || result.result?.reason || result.result?.preview?.reason || "-";
  setHtml("actionResultSummary", `
    <div class="status-line">
      ${chip(ok ? "실행 완료" : "실행 실패", ok ? "ok" : "danger")}
      ${chip("라이브", "danger")}
      ${chip(modeLabel(result.mode || result.result?.mode || "action"), "warn")}
    </div>
    <dl class="key-value-list">
      ${row("사유", reasonLabel(reason))}
      ${row("종목", result.symbol || result.result?.symbol || result.recommendation?.symbol)}
      ${row("상태", orderStatusLabel(result.final_status || result.result?.final_status || result.result?.status))}
    </dl>
  `);
  setText("actionResult", json(result));
}

async function requestJson(url, options = {}) {
  const method = options.method || "GET";
  const requestUrl = method === "GET" ? `${url}${url.includes("?") ? "&" : "?"}_ts=${Date.now()}` : url;
  const response = await fetch(requestUrl, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    const error = new Error(payload.detail || payload.reason || payload.error || `Request failed: ${response.status}`);
    error.payload = payload;
    throw error;
  }
  return payload;
}

function render() {
  const payload = state.payload;
  if (!payload) return;

  const snapshot = payload.snapshot || {};
  const process = payload.autonomous_process || {};
  const account = snapshot.account || {};
  const paper = snapshot.paper_decision || {};
  const op = snapshot.operational_summary || {};
  const lastExec = snapshot.last_execution_report || {};
  const lastAuto = snapshot.last_autonomous_report || {};
  const positions = enrichPositions(snapshot);
  const riskGate = paper.risk_gate || {};
  const investedSymbols = positions.map((item) => item.symbol);

  const totalCapital = num(account.account?.account_equity) || 0;
  const investedCapital = num(paper.current_invested_notional) || 0;
  const remainingCapital = num(account.account?.wallet_balance) || 0;
  const currentProfit = num(account.account?.unrealized_pnl) || 0;
  const profitRate = investedCapital > 0 ? (currentProfit / investedCapital) * 100 : 0;
  const riseProbability = average(positions.map((item) => item.riseProbability))
    ?? average((paper.recommendations || []).map((item) => item.profit_potential))
    ?? 0;
  const actualRate = average(positions.map((item) => item.actualChangeRate)) ?? 0;
  const blockedByRisk = !!riskGate.block_new_entries;
  const lastCycleTs = shortTs(lastAuto.payload?.ts);

  setHtml("progressStatus", `
    <div class="status-line">
      ${chip(process.running ? "자동매매 실행 중" : "자동매매 중지", process.running ? "ok" : "warn")}
      ${chip(blockedByRisk ? "신규 진입 차단" : "신규 진입 가능", blockedByRisk ? "danger" : "ok")}
      ${chip(`최근 사이클 ${lastCycleTs}`, "warn")}
    </div>
    <dl class="key-value-list">
      ${row("현재 단계", process.running ? "자동매매 루프가 추천 선정과 자동 실행을 계속 처리 중입니다." : "대기 상태")}
      ${row("관리 종목 수", lastAuto.payload?.state_after?.managed_position_count ?? paper.active_position_count)}
      ${row("자동 진입 후보 수", (paper.recommendations || []).length)}
      ${row("차단 사유", blockedByRisk ? (riskGate.decision_line || reasonLabel(riskGate.reason)) : "없음")}
    </dl>
  `);

  setHtml("processStatus", `
    <div class="status-line">
      ${chip(process.running ? "자동매매 실행 중" : "자동매매 중지", process.running ? "ok" : "warn")}
      ${chip("라이브 프로세스", "danger")}
    </div>
    <dl class="key-value-list">
      ${row("PID", process.pid)}
      ${row("모드", modeLabel(process.mode))}
      ${row("시작 시각", shortTs(process.started_at))}
    </dl>
  `);

  setHtml("operationalSummary", metricGrid([
    { label: "프로파일", value: op.selected_profile },
    { label: "시장 상태", value: op.market_regime },
    { label: "최우선 종목", value: op.top_selected_symbol },
    { label: "선정 종목 수", value: op.selected_symbol_count },
  ]) + `
    <dl class="key-value-list">
      ${row("백테스트 수익률", pct(op.benchmark_final_pnl_percent))}
      ${row("백테스트 최대낙폭", pct(op.benchmark_max_drawdown_percent))}
      ${row("선택 사유", op.reason || op.decision_line)}
    </dl>
  `);

  setHtml("lastExecution", `
    <div class="status-line">
      ${chip(modeLabel(lastExec.mode || "no_execution_report"), lastExec.executed ? "ok" : "warn")}
      ${chip(lastExec.executed ? "실행됨" : "미실행", lastExec.executed ? "ok" : "warn")}
    </div>
    <dl class="key-value-list">
      ${row("요약", lastExec.short_summary || lastExec.alert_summary || reasonLabel(lastExec.reason))}
      ${row("종목", lastExec.symbol || lastExec.payload?.symbol)}
    </dl>
  `);

  setHtml("lastAutonomous", metricGrid([
    { label: "진입", value: lastAuto.entry_count },
    { label: "청산", value: lastAuto.exit_count },
    { label: "관리 중", value: lastAuto.payload?.state_after?.managed_position_count },
    { label: "모드", value: modeLabel(lastAuto.mode) },
  ]) + `
    <dl class="key-value-list">
      ${row("요약", lastAuto.decision_line)}
      ${row("시각", shortTs(lastAuto.payload?.ts))}
    </dl>
  `);

  setHtml("accountSummary", metricGrid([
    { label: "총자금", value: money(totalCapital) },
    { label: "투자금", value: money(investedCapital) },
    { label: "잔여금", value: money(remainingCapital) },
    { label: "현재 손익금", value: money(currentProfit) },
    { label: "손익률", value: pct(profitRate) },
    { label: "투자 종목", value: investedSymbols.length ? investedSymbols.join(", ") : "-" },
    { label: "평균 상승률", value: pct(riseProbability) },
    { label: "현재 변동률", value: pct(actualRate) },
  ]) + `
    <dl class="key-value-list">
      ${row("목표 투자금", money(paper.target_invested_capital))}
      ${row("종목별 목표 투자금", money(paper.target_allocation_per_symbol))}
    </dl>
  `);

  setHtml("paperDecision", `
    <div class="status-line">
      ${chip((paper.recommendations || []).length ? "자동 진입 준비" : "자동 진입 없음", (paper.recommendations || []).length ? "ok" : "warn")}
      ${chip(riskGate.ok ? "리스크 게이트 통과" : "리스크 게이트 차단", riskGate.ok ? "ok" : "danger")}
    </div>
    <dl class="key-value-list">
      ${row("자동 진입 후보 수", (paper.recommendations || []).length)}
      ${row("차단 개수", (paper.blocked || []).length)}
      ${row("활성 포지션", paper.active_position_count)}
      ${row("남은 슬롯", paper.available_slots)}
      ${row("목표 종목 수", paper.target_symbol_count)}
      ${row("종목별 목표 투자금", money(paper.target_allocation_per_symbol))}
      ${row("자금 사용률", pct(paper.capital_utilization_percent))}
      ${row("판정", paper.decision_line)}
    </dl>
  `);

  renderTopRecommendation(paper);
  renderActionResult();
  setHtml("activePositions", positionsTable(positions));
  setHtml("riskGateSummary", riskGateSummary(riskGate));
  setText("riskGate", json(riskGate));
}

async function refreshStatus(force = false) {
  if (state.refreshInFlight) return;
  state.refreshInFlight = true;
  try {
    if (force) message("상태를 강제로 갱신하고 있습니다...");
    const url = force ? "/api/status/refresh" : "/api/status";
    const options = force ? { method: "POST", body: "{}" } : {};
    state.payload = await requestJson(url, options);
    render();
    if (force) message("상태가 갱신되었습니다.");
  } catch (error) {
    message(error.message, true);
  } finally {
    state.refreshInFlight = false;
  }
}

function requireLiveConfirmation(label) {
  return window.confirm(`${label} 작업은 실제 라이브 주문으로 진행됩니다. 계속하시겠습니까?`);
}

async function runAction(label, requestFactory, successMessage) {
  try {
    if (!requireLiveConfirmation(label)) {
      message(`${label} 작업이 취소되었습니다.`);
      return;
    }
    message(`${label} 작업을 실행하고 있습니다...`);
    const result = await requestFactory();
    state.actionResult = result;
    renderActionResult();
    message(successMessage(result));
    await refreshStatus(true);
  } catch (error) {
    state.actionResult = error.payload || { ok: false, reason: error.message };
    renderActionResult();
    message(error.message, true);
  }
}

async function startAutonomous() {
  await runAction(
    "라이브 시작",
    () => requestJson("/api/autonomous/start", {
      method: "POST",
      body: JSON.stringify({ live: true, adopt_active_positions: true, interval_seconds: 60 }),
    }),
    (result) => `자동매매 라이브 프로세스를 시작했습니다. pid=${fmt(result.pid)}`
  );
}

async function stopAutonomous() {
  await runAction(
    "자동 중지",
    () => requestJson("/api/autonomous/stop", { method: "POST", body: "{}" }),
    (result) => result.stopped ? `자동매매 프로세스 ${fmt(result.pid)}를 중지했습니다.` : reasonLabel(result.reason)
  );
}

async function runHealthCheck() {
  await runAction(
    "라이브 헬스체크",
    () => requestJson("/api/actions/health-check", {
      method: "POST",
      body: JSON.stringify({
        symbol: "BTCUSDT",
        side: "BUY",
        quantity: 0.001,
        live: true,
      }),
    }),
    (result) => {
      const openStatus = result.result?.open_result?.final_status || "-";
      const closeStatus = result.result?.close_result?.final_status || "-";
      return `헬스체크 완료. 진입=${openStatus} 청산=${closeStatus}`;
    }
  );
}

async function stopAndCloseAll() {
  await runAction(
    "전체 청산 및 중지",
    () => requestJson("/api/actions/stop-and-close-all", {
      method: "POST",
      body: JSON.stringify({ live: true }),
    }),
    () => "전체 청산 및 중지 요청이 완료되었습니다."
  );
}

function bind(id, eventName, handler) {
  const node = el(id);
  if (node) node.addEventListener(eventName, handler);
}

function init() {
  bind("refreshBtn", "click", () => refreshStatus(true));
  bind("startLiveBtn", "click", startAutonomous);
  bind("stopBtn", "click", stopAutonomous);
  bind("healthBtn", "click", runHealthCheck);
  bind("closeAllBtn", "click", stopAndCloseAll);
  renderActionResult();
  message("상태를 불러오는 중입니다...");
  refreshStatus(true);
  window.setInterval(() => refreshStatus(false), 3000);
}

window.addEventListener("load", init);
