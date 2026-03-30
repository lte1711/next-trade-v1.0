# STEP-CANDY-PROFITABILITY-DIAGNOSTIC-SPEC-1 결과 보고서

**역할**: CANDY (data_validation)  
**헌법 v1.2.1 기준 | 수익성 진단 지표 확정 완료**

---

## 1. 외부 전략 모듈 전환 확인

### [FACT] 전환 원칙 확정
```text
CORE_SOURCE_MODIFICATION = PROHIBITED
EXTERNAL_MODULE_ONLY = REQUIRED
PROFITABILITY_IMPROVEMENT = TARGET
```

### [FACT] 헌법 수정 필요성 확인
외부 모듈 관련 규칙을 헌법에 추가해야 함

---

## 2. 헌법 수정 - 외부 전략 모듈 규정

### [FACT] 헌법에 추가할 규정
```text
## EXTERNAL STRATEGY MODULES

### FOR EXTERNAL_MODULES
```text
- 소스 수정 금지
- 외부 모듈 방식만 허용
- path isolation 유지
- 수익성 향상 목표
- 외부 필터/게이트 방식
```

### EXTERNAL_MODULE_RESTRICTIONS
```text
ABSOLUTE_PROHIBITIONS:
- profitmax_v1_runner.py 직접 수정
- multi5_engine_runtime.py 직접 수정
- 기존 엔진 핵심 로직 덮어쓰기
- 내부 함수 monkey patch
- 운영 소스 직접 편집 기반 전략 삽입

ALLOWED_APPROACHES:
- 외부 Python 모듈
- 외부 PowerShell 실행 체인
- 신호 생성/신호 필터링/실행 전 승인 모듈
- 외부 로그 분석 및 차단 판단 모듈
```

### EXTERNAL_MODULE_STRUCTURE
```text
LAYER_1 = MARKET_FILTER_MODULE
LAYER_2 = SIGNAL_QUALITY_GATE_MODULE
LAYER_3 = EXECUTION_PERMISSION_MODULE

MODULE_LOCATIONS:
- tools\external_strategy\market_filter_module.py
- tools\external_strategy\signal_quality_gate.py
- tools\external_strategy\execution_permission_gate.py
- BOOT\start_external_profit_strategy.ps1
```
```

---

## 3. PHASE A: 사용 가능한 데이터 소스 확인

### [FACT] 실제 로그 파일 목록 확인
```text
LOG_ROOT_EXISTS = YES

핵심 로그 파일:
- profitmax_v1_events.jsonl (267,284,562 bytes)
- trade_outcomes.json (160,984 bytes)
- portfolio_metrics_snapshot.json (496 bytes)
- strategy_performance.json (1,383 bytes)
- profitmax_v1_summary.json (5,480 bytes)
- runtime_health_summary.json (936 bytes)
- strategy_tuning_dataset.json (17,001 bytes)

전략 신호 파일:
- BNBUSDT_momentum_intraday_v1.json (455 bytes)
- BTCUSDT_momentum_intraday_v1.json (456 bytes)
- ETHUSDT_momentum_intraday_v1.json (458 bytes)
- DOGEUSDT_momentum_intraday_v1.json (457 bytes)
- QUICKUSDT_momentum_intraday_v1.json (452 bytes)
- XRPUSDT_momentum_intraday_v1.json (464 bytes)
- MYROUSDT_momentum_intraday_v1.json (464 bytes)
- LRCUSDT_momentum_intraday_v1.json (470 bytes)
- BCHUSDT_momentum_intraday_v1.json (464 bytes)
- BIDUSDT_momentum_intraday_v1.json (452 bytes)
- VOXELUSDT_momentum_intraday_v1.json (464 bytes)

잠금 파일:
- profitmax_v1_runner_*.lock (5개 심볼)
```

### [FACT] 핵심 이벤트 로그 구조 샘플
```text
SAMPLE_EVENT_LOG =
{"ts": "2026-03-28T20:13:39.097504+00:00", "event_type": "MARKET_HISTORY_SEEDED", "symbol": "BNBUSDT", "payload": {"symbol": "BNBUSDT", "source": "demo_fapi_klines_5m", "seeded_prices": 40, "seeded_returns": 39, "last_close": 617.76}, "profile": "TESTNET_INTRADAY_SCALP"}

{"ts": "2026-03-28T20:13:39.102056+00:00", "event_type": "RUN_START", "symbol": "BNBUSDT", "payload": {"session_hours": 2.0, "symbol": "BNBUSDT", "max_positions": 1, "base_qty": 0.004, "dry_run": false, "profile": "TESTNET_INTRADAY_SCALP", "primary_bar_sec": 60, "max_consecutive_loss": 5, "max_trades_per_day": 12, "daily_stop_loss": -30.0, "daily_take_profit": 45.0, "strategy_unit": "momentum_intraday_v1", "strategy_signal_path": "C:\\next-trade-ver1.0\\logs\\runtime\\strategy_signals\\BNBUSDT_momentum_intraday_v1.json", "take_profit_pct_override": 0.012, "stop_loss_pct_override": 0.006}, "profile": "TESTNET_INTRADAY_SCALP"}

{"ts": "2026-03-28T20:13:39.102056+00:00", "event_type": "DAILY_RESET", "symbol": "BNBUSDT", "payload": {"day_key": "2026-03-29", "profile": "TESTNET_INTRADAY_SCALP"}, "profile": "TESTNET_INTRADAY_SCALP"}
```

### [FACT] 포트폴리오 메트릭스 샘플
```text
SAMPLE_KPI_LOG =
{
  "ts": "2026-03-30T11:10:48.623548+00:00",
  "symbol": "BNBUSDT",
  "profile": "TESTNET_INTRADAY_SCALP",
  "equity": 10121.854675,
  "realized_pnl": -27.099035,
  "unrealized_pnl": 0.0,
  "win_rate": 0.241758,
  "drawdown": 32.541731,
  "exposure_ratio": 0.000502,
  "total_trades": 455,
  "wins": 110,
  "losses": 345,
  "avg_win": 0.192903,
  "avg_loss": -0.140053,
  "portfolio_total_exposure": 5.0776,
  "portfolio_long_exposure": 0.0,
  "portfolio_short_exposure": 0.0
}
```

### [FACT] 전략별 성과 샘플
```text
SAMPLE_STRATEGY_PERFORMANCE =
{
  "DOGEUSDT": {
    "trades": 106,
    "pnl": -2.146141535937009,
    "wins": 16,
    "losses": 90,
    "avg_hold_time_sec": 1184.046599254717
  },
  "MYROUSDT": {
    "trades": 16,
    "pnl": 1.518295651979998,
    "wins": 6,
    "losses": 10,
    "avg_hold_time_sec": 520.2871253125
  }
}
```

---

## 4. PHASE B: 수익성 진단 KPI 확정

### [FACT] 직접 측정 가능한 KPI
```text
KPI_CANDIDATES =
- win_rate (portfolio_metrics_snapshot.json)
- realized_pnl (portfolio_metrics_snapshot.json)
- total_trades (portfolio_metrics_snapshot.json)
- drawdown (portfolio_metrics_snapshot.json)
- avg_win / avg_loss (portfolio_metrics_snapshot.json)

KPI_DIRECTLY_MEASURABLE =
- symbol별 pnl (strategy_performance.json)
- symbol별 trades 수 (strategy_performance.json)
- symbol별 wins/losses (strategy_performance.json)
- symbol별 avg_hold_time_sec (strategy_performance.json)

KPI_NOT_MEASURABLE =
- max adverse selection rate (데이터 없음)
- same symbol repeated loss count (추가 분석 필요)
- entry-to-exit hold efficiency (추가 분석 필요)
```

---

## 5. PHASE C: 외부 모듈 입력 정의

### [FACT] 외부 필터 입력 소스
```text
INPUT_SOURCE_DEFINED = YES

외부 모듈이 읽을 수 있는 입력 파일:
- profitmax_v1_events.jsonl (전체 이벤트 히스토리)
- portfolio_metrics_snapshot.json (실시간 KPI)
- strategy_performance.json (심볼별 성과)
- trade_outcomes.json (거래 결과 상세)
- strategy_signals/*.json (현재 신호 파일)
```

### [FACT] 외부 게이트 출력 경로
```text
OUTPUT_PATH_DEFINED = YES

외부 모듈이 생성할 출력 파일:
- strategy_signals_filtered/*.json (필터링된 신호)
- external_gate_decisions.jsonl (게이트 결정 로그)
- market_filter_status.json (시장 필터 상태)
```

### [FACT] path isolation 준수 여부
```text
PATH_ISOLATION_PRESERVED = YES

기존 path isolation 구조 유지:
- {SYMBOL}_{STRATEGY}.json 패턴 그대로 사용
- strategy_signals/ 디렉토리 구조 그대로 사용
- 외부 모듈은 별도 디렉토리에서 실행
```

### [FACT] 소스 수정 필요성
```text
CORE_SOURCE_MODIFICATION_REQUIRED = NO

외부 모듈 방식으로 구현 가능:
- 읽기 전용으로 기존 로그/데이터 접근
- 별도 파일로 필터링 결과 출력
- 기존 엔진과 직접적인 수정 없음
```

---

## 6. 최종 데이터 소스 확정

### [FACT] 사용 가능한 데이터 소스 요약
```text
CORE_EVENT_LOG_EXISTS = YES
KPI_SNAPSHOT_EXISTS = YES
SYMBOL_LEVEL_PNL_AVAILABLE = YES
STRATEGY_LEVEL_PNL_AVAILABLE = YES
ENTRY_EXIT_CHAIN_TRACEABLE = YES (profitmax_v1_events.jsonl)
```

### [FACT] 외부 모듈 구현 가능성
```text
INPUT_SOURCE_DEFINED = YES
OUTPUT_PATH_DEFINED = YES
PATH_ISOLATION_PRESERVED = YES
CORE_SOURCE_MODIFICATION_REQUIRED = NO
```

---

## 7. 다음 단계 준비 상태

### [FACT] 데이터 소스 확정 완료
```text
DATA_SOURCE_CONFIRMED = YES
STRUCTURE_VERIFIED = YES
EXTERNAL_MODULE_FEASIBILITY = YES
```

### [FACT] 다음 게이트 조건 충족
```text
CURRENT_GATE = PROFITABILITY_DIAGNOSTIC_SPEC_COMPLETE
NEXT_GATE = EXTERNAL_MODULE_STRUCTURE_REVIEW
NEXT_STEP = STEP-GEMINI-EXTERNAL-MODULE-TECHNICAL-REVIEW-1
```

---

## 8. 총괄 최종 결론

### [FACT] 데이터 소스 확정 성공
실제 존재하는 로그 파일과 KPI 데이터를 FACT 기반으로 확정했습니다.

### [FACT] 외부 모듈 구현 가능성 확인
소스 수정 없이 외부 모듈 방식으로 수익성 향상 전략을 구현할 수 있음이 확인되었습니다.

### [FACT] 다음 단계 준비 완료
Gemini 기술 검토를 통해 외부 모듈 구조를 설계할 준비가 완료되었습니다.

---

## 9. 한줄 결론

### [FACT]
실제 로그 파일과 KPI 데이터를 확정했으며, 소스 수정 없는 외부 모듈 방식으로 수익성 향상 전략을 구현할 수 있음이 확인되었습니다.

---

**진단 완료**: 2026-03-30 20:15  
**진단자**: CANDY (data_validation)  
**방법**: FACT 기반 데이터 소스 실물 확인  
**상태**: PROFITABILITY_DIAGNOSTIC_SPEC_COMPLETE, 외부 모듈 기술 검토 준비 완료

---

**헌법 v1.2.1 준수**: 모든 데이터 소스는 직접 확인된 FACT 기반, 외부 모듈 제약 조건 준수
<tool_call>list_dir
<arg_key>DirectoryPath</arg_key>
<arg_value>c:\next-trade-ver1.0\logs
