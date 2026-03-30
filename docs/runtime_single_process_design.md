# Runtime Single-Process Design

## Goal

Reduce misleading `2-process` role pairs where it is safe, while keeping the `127.0.0.1:8787` dashboard and the current live runtime stable.

This is a design document, not an immediate migration script.

## Current State

Observed effective runtime chain:

- `dashboard_8787`
- `api_8100`
- `multi5_engine`
- `worker:BCHUSDT`
- `worker:DOGEUSDT`
- `worker:QUICKUSDT`

Observed raw process count is higher because several roles appear as parent/child pairs.

Current dashboard already exposes:

- `effective_role_count`
- `raw_runtime_process_count`
- `process_roles`

Relevant implementation:

- `tools/dashboard/multi5_dashboard_server.py`
- `tools/dashboard/multi5_dashboard.html`

## Findings

### 1. Engine and workers are launched by wrapper scripts

`BOOT/start_engine.ps1` starts:

- `.venv\Scripts\python.exe`
- target: `tools\multi5\run_multi5_engine.py`

`tools/multi5/run_multi5_engine.py` then starts workers with:

- `.venv\Scripts\python.exe`
- target: `tools\ops\profitmax_v1_runner.py`
- implementation: `subprocess.Popen(...)`

This means the engine is intentionally a long-running launcher and workers are intentionally child processes of that launcher.

### 2. API is launched through a cmd wrapper

`tools/ops/run_api_8100.cmd` starts:

- `.venv\Scripts\python.exe -m uvicorn next_trade.api.app:app --port 8100`

In the current Windows environment this shows as a visible parent/child chain in process inspection.

### 3. Dashboard is launched by a PowerShell starter

`BOOT/start_dashboard_8787.ps1` starts:

- `.venv\Scripts\python.exe`
- target: `tools\dashboard\multi5_dashboard_server.py`

The dashboard itself is single-role, but the launch path is still wrapper-driven.

### 4. Autoguard assumes wrapper-driven startup

`BOOT/phase5_autoguard.ps1` continuously ensures:

- engine
- api
- dashboard
- validation monitors
- milestone observers
- workers for open positions

Because autoguard is written against current wrapper patterns, changing process structure without changing autoguard would be risky.

## Design Principle

Do not treat every 2-process pair as a bug.

There are two different cases:

1. Real duplicate runtime:
- two independent dashboards on the same role
- two independent APIs
- two workers for the same symbol

2. Execution chain:
- one wrapper or launcher
- one effective runtime process

Only case 1 should be killed immediately.
Case 2 should be migrated by code and boot-chain redesign.

## Recommended Plan

### Phase A. Keep current runtime, improve visibility

Status: already done.

Keep `8787` as the control surface and show:

- raw count
- effective count
- grouped roles
- PID list per role

Success condition:

- operators can distinguish duplicate runtime from parent/child execution chains

### Phase B. Normalize process identity before reducing process count

Add explicit metadata for each launched role:

- role name
- symbol if worker
- launcher pid
- child pid if known
- start source script

Recommended implementation:

- write a small runtime registry JSON under `logs/runtime/process_registry.json`
- update `run_multi5_engine.py` to record worker launches
- update `start_dashboard_8787.ps1` and API starter path to record launch source

Success condition:

- `8787/api/runtime` can report role identity without relying only on command-line parsing

### Phase C. API startup simplification

This is the safest first simplification candidate.

Current:

- `phase5_autoguard.ps1` calls `cmd.exe /c tools\ops\run_api_8100.cmd`

Recommended target:

- replace `run_api_8100.cmd` with a PowerShell-native starter
- launch Python directly from PowerShell
- keep one documented startup path

Why first:

- API is not symbol-scoped
- easier to verify with port `8100`
- lower risk than worker lifecycle changes

Success condition:

- one startup path for API
- no duplicate API launchers
- autoguard still restores API correctly

### Phase D. Dashboard startup simplification

Current:

- `start_dashboard_8787.ps1` launches Python directly

Recommended target:

- keep PowerShell starter
- standardize it as the only dashboard launcher
- add a PID file and health probe contract

This phase is mostly cleanup, not major architecture change.

Success condition:

- dashboard role is uniquely tracked
- restart logic uses PID file + port health, not only process pattern matching

### Phase E. Worker lifecycle redesign

This is the highest-risk area and should be done last.

Current:

- engine wrapper launches workers with `subprocess.Popen(...)`
- autoguard may also start workers for open symbols
- worker liveness is inferred from process scan, lock files, and event freshness

Recommended target:

- choose exactly one owner of worker lifecycle

Two options:

1. Engine-owned workers
- only `run_multi5_engine.py` starts/stops workers
- autoguard monitors but does not spawn workers

2. Supervisor-owned workers
- autoguard or a dedicated supervisor starts/stops workers
- engine only ranks symbols and writes desired state

Recommended choice:

- Engine-owned workers

Reason:

- symbol selection and worker spawning are already colocated in `run_multi5_engine.py`
- fewer cross-script races

Required changes:

- remove worker spawn responsibility from `phase5_autoguard.ps1`
- convert autoguard worker logic into monitor-only alerts
- keep lock files, but make engine the only writer

Success condition:

- one worker owner
- no split-brain worker starts
- worker count equals selected/open-symbol intent

### Phase F. Optional engine internalization

If we later want fewer visible processes, the engine can move from spawning external worker processes to managing in-process worker tasks.

Do not do this now.

Reason:

- biggest behavioral change
- highest regression risk
- harder recovery semantics

## What Should Not Be Done Now

- Do not blindly kill one process from each parent/child pair.
- Do not remove autoguard before startup ownership is redesigned.
- Do not merge worker logic into one process during active live runtime.

## Proposed Implementation Order

1. Keep current runtime and dashboard visibility.
2. Replace API `.cmd` startup with one PowerShell-native path.
3. Add PID/registry tracking for dashboard and API.
4. Refactor autoguard so worker spawning is monitor-only.
5. Make `run_multi5_engine.py` the single worker owner.
6. Reassess whether remaining parent/child pairs are acceptable.

## Immediate Next Change Recommendation

If we want to start implementation safely, begin with:

- API startup path normalization

This gives a real simplification win with the lowest operational risk.
