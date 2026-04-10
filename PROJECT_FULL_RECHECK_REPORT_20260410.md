# NEXT-TRADE Full Recheck Report - 2026-04-10

## 1. 결론

현재 운영 경로 기준 핵심 시스템은 정상 동작 가능 상태다.

- 런타임 초기화: 정상
- Binance Futures demo/testnet 연결: 정상
- 현재 활성 포지션: 0개
- 현재 미체결 주문: 0개
- 시스템 에러: 0개
- 유효 동적 심볼: 50개
- 활성 전략: `ma_trend_follow`, `ema_crossover`
- 핵심 파이썬 파일 컴파일: 통과
- pytest: 현재 `.venv`에 `pytest`가 없어 실행 불가

오늘 진화의 핵심 결과는 3가지다.

- 의미 없는 심볼 필터가 신규 진입뿐 아니라 기존 보유에도 대칭 적용된다.
- `NEIROUSDT`, `ZRCUSDT` 등 기준 미달 포지션이 실제 테스트넷에서 청산 완료됐다.
- `NEW -> FILLED`로 늦게 확정되는 reduce-only 청산 주문의 realized PnL 누락을 자동 보정하는 리컨실리에이션 로직이 추가됐다.

## 2. 현재 실증 상태

실제 테스트넷 조회 기준:

- `base_url`: `https://demo-fapi.binance.com`
- `active_positions`: `{}`
- `open_order_count`: `0`
- `available_balance`: 약 `8623.39 USDT`
- `valid_symbols_count`: `50`
- `system_errors_count`: `0`

저널 상태:

- `real_orders_count`: `47`
- `realized_pnl_journal_count`: `27`
- 성과 추적 심볼: `AKEUSDT`, `FUNUSDT`, `NEIROUSDT`, `REIUSDT`, `ZRCUSDT`

중요 증거 파일:

- `EXECUTE_FIRST_CHECKPOINT_20260410_STEP26_STRICT_HOLD_CLOSE_ALL.json`
- `EXECUTE_FIRST_CHECKPOINT_20260410_STEP26_STRICT_HOLD_CLOSE_ALL_SYNC_VERIFY.json`
- `EXECUTE_FIRST_CHECKPOINT_20260410_STEP26_ORPHAN_OPEN_ORDER_CLEANUP.json`
- `EXECUTE_FIRST_CHECKPOINT_20260410_STEP27_REDUCE_ONLY_RECONCILIATION.json`

## 3. 전체 실행 플로우

```text
config.json / .env
  -> TradingRuntime 초기화
  -> API 키, base_url, trading_config 로드
  -> AccountService / MarketDataService / IndicatorService / MarketRegimeService 생성
  -> SignalEngine / StrategyRegistry / AllocationService 생성
  -> OrderExecutor / ProtectiveOrderManager / PositionManager 생성
  -> TradeOrchestrator 생성
  -> account sync + position sync
  -> valid_symbols 50개 로드
  -> run_trading_cycle 반복
```

한 사이클 내부:

```text
계정/포지션 동기화
  -> 시장 데이터 갱신
  -> 전략별 후보 심볼 선택
  -> 1h 가격/거래량 기반 시장 레짐 분석
  -> 지표 계산
  -> 심볼 품질 필터
  -> 신호 생성
  -> 후보 점수화
  -> 중복/한도/잔고 확인
  -> 동적 포지션 크기 산정
  -> 주문 제출
  -> 보호 주문 배치
  -> 열린 포지션 관리
  -> pending reduce-only 체결 리컨실리에이션
  -> trading_results.json 저장
```

## 4. 모듈별 로직 설명

### 4.1 `main_runtime.py`

역할: 전체 런타임 조립자다.

주요 흐름:

- `.env`와 `config.json`에서 API 정보와 거래 설정을 읽는다.
- `TradingRuntime.__init__()`에서 모든 서비스 객체를 만든다.
- `account_service.periodic_sync()`로 계정 잔고를 읽고 `available_balance`를 갱신한다.
- `load_valid_symbols()`로 Binance demo futures에서 거래 가능한 상위 심볼을 가져온다.
- `run()` 루프에서 `trade_orchestrator.run_trading_cycle()`을 호출한다.
- `_process_cycle_results()`에서 결과를 `trading_results`에 반영하고 파일로 저장한다.
- 새로 추가된 `order_executor.reconcile_pending_reduce_only_fills()`가 저장 직전 실행된다.

판단:

- 런타임 초기화는 정상이다.
- 현재 상태 조회에서 포지션과 미체결 주문 모두 0개다.
- 단, `config.json`에 API 키와 시크릿이 평문으로 들어 있다. 테스트넷이라도 보안상 `.env`만 사용하고 config 내 키는 제거하는 것이 좋다.

### 4.2 `core/account_service.py`

역할: 계정 정보, 잔고, 포지션 동기화 담당.

주요 로직:

- `/fapi/v2/account` 계열 서명 요청으로 계정 정보를 가져온다.
- `sync_account_balance()`가 `account_balance`, `total_balance`, `available_balance`를 갱신한다.
- `sync_positions()`가 거래소 포지션을 읽고 `active_positions`를 재구성한다.
- 기존 로컬 포지션 메타데이터를 최대한 보존한다.
- `can_open_new_positions()`는 포지션 수 한도와 최소 잔고 기준을 확인한다.

판단:

- 5초 위치 동기화 간격으로 실제 계정 변화 반영 속도는 충분하다.
- 현재 동기화 결과는 active 0개로 정상이다.

### 4.3 `core/market_data_service.py`

역할: 현재가, kline, 동적 심볼 목록 제공.

주요 로직:

- `get_current_price()`는 단일 심볼 현재가를 조회한다.
- `update_market_data()`는 각 심볼에 대해 현재가와 `1m`, `5m`, `15m`, `1h` kline을 가져온다.
- `get_available_symbols()`는 `exchangeInfo`와 `24hr ticker`를 조합해 USDT perpetual, TRADING 상태만 고른다.
- 가격이 너무 낮은 심볼은 `_min_symbol_price` 기준으로 필터된다.
- 거래량 기준 상위 50개를 캐시한다.

판단:

- `MYROUSDT` 같은 의미 없는 심볼을 완전히 막는 핵심 1차 방어선은 여기가 아니라 `TradeOrchestrator._evaluate_symbol_quality()`다.
- 시장 데이터 단계는 후보군을 넓게 가져오고, 품질 판단은 이후 단계에서 한다.

### 4.4 `core/indicator_service.py`

역할: 기술 지표 계산 담당.

주요 로직:

- SMA, EMA, RSI, ATR 계산.
- Heikin Ashi 캔들 및 패턴 분석.
- 프랙탈 고점/저점 계산.

판단:

- 진입 판단에 직접 쓰이는 `price_vs_sma_pct`, `volume_ratio` 등은 현재 `TradeOrchestrator._calculate_symbol_indicators()`에서 조합된다.

### 4.5 `core/market_regime_service.py`

역할: 시장 국면과 추세/변동성 판단.

주요 로직:

- `analyze_market_regime()`가 ADX, 변동성, 모멘텀을 계산한다.
- `BULL_TREND`, `BEAR_TREND`, `HIGH_VOLATILITY`, `RANGING`으로 분류한다.
- `analyze_timeframe_ma()`가 이동평균 기반 위치를 분석한다.

판단:

- 현재 품질 필터에서 `trend_strength`, `volatility_level`, `regime`이 핵심 입력으로 사용된다.

### 4.6 `core/signal_engine.py`

역할: 전략 신호 생성과 후보 점수화.

주요 로직:

- `generate_strategy_signal()`은 현재가와 SMA 비교로 `BUY`, `SELL`, `HOLD`를 만든다.
- `price_vs_sma`가 양수면 매수, 음수면 매도 성향을 본다.
- `_calculate_dynamic_confidence()`가 고정 confidence 대신 동적 confidence를 만든다.
- confidence 요소는 가격 괴리, 거래량 비율, 추세강도, 시장 레짐 정렬, 변동성 패널티다.
- `score_trade_candidate()`는 confidence, 방향 보너스, 괴리 점수, 거래량 점수, 레짐 점수, 리스크 보너스, 변동성 패널티를 합쳐 후보 점수를 만든다.
- `get_signal_statistics()`의 엔진 타입은 `DYNAMIC_MARKET_QUALITY_SCORING`이다.

판단:

- 예전보다 시장 상태를 더 많이 반영한다.
- 다만 기본 `minimal_thresholds.min_confidence=0.1`은 여전히 낮다. 실질적인 방어는 품질 필터와 점수화에서 담당한다.

### 4.7 `core/strategy_registry.py`

역할: 전략 정의와 전략별 심볼 선택.

주요 로직:

- 현재 전략은 `ma_trend_follow`, `ema_crossover` 2개다.
- 두 전략 모두 `max_open_positions=10`으로 설정되어 있다.
- `select_preferred_symbols()`는 상위 후보군에서 전략별 최대 10개를 선택한다.
- `leaders`, `volatile`, `pullback`, `balanced` 모드를 지원한다.

판단:

- 지금은 기본적으로 leaders 모드라 거래량 상위권이 우선이다.
- 10개 포지션 확장 요구는 코드상 반영되어 있다.

### 4.8 `core/allocation_service.py`

역할: 동적 포지션 크기 산정.

주요 로직:

- `calculate_position_size()`가 전략 자본, 신호 confidence, 변동성, ATR, 전략 config, `allocation_context`를 받아 포지션 크기를 계산한다.
- confidence multiplier, regime multiplier, trend multiplier, volume multiplier, exposure multiplier, performance multiplier를 곱해 `quality_multiplier`를 만든다.
- 레짐과 신호 방향이 맞으면 증액하고, 반대면 감액한다.
- 이미 포지션이 많으면 exposure multiplier가 줄어든다.
- 심볼별 과거 손익이 나쁘면 performance multiplier가 줄어든다.
- legacy `max_position_size=0.02` 같은 비율값은 USDT 캡으로 오해하지 않도록 방어되어 있다.

판단:

- STEP17에서 FUNUSDT 실제 진입에 동적 allocation이 기록됐고, 이후 realized PnL 리컨실리에이션으로 심볼 성과 데이터가 보강됐다.

### 4.9 `core/trade_orchestrator.py`

역할: 한 거래 사이클의 중앙 오케스트레이터.

주요 로직:

- `run_trading_cycle()`이 전체 사이클을 실행한다.
- 계정 동기화 후 시장데이터를 업데이트한다.
- 전략별 선호 심볼을 선택한다.
- 각 심볼의 지표와 레짐을 계산한다.
- `_evaluate_symbol_quality()`로 심볼 품질을 평가한다.
- 신규 진입 기준과 보유 기준 모두 `len(reasons) == 0 and not critical_reasons`다.
- 품질 탈락 이유는 `flat_price_vs_sma`, `thin_recent_volume`, `weak_trend_strength`, `very_low_volatility`, `unknown_market_regime`으로 분류된다.
- 거래량이 0.05 미만이면 `critically_thin_recent_volume`으로 강한 탈락 사유가 붙는다.
- 중복 포지션/중복 pending을 막는다.
- 후보 점수에 심볼별 과거 성과 bias를 반영한다.
- `execute_strategy_trade()`가 포지션 사이징, 주문 제출, 보호 주문 배치, position journal 기록을 수행한다.

판단:

- `MYROUSDT`, `ZRCUSDT` 같은 문제가 있던 심볼이 들어온 이유는 이전에는 보유 조건이 약점 1개까지 허용했기 때문이다.
- 현재는 신규 진입과 보유 조건이 대칭으로 강화되었으므로, 약점이 1개라도 있으면 신규 진입/보유 모두 탈락한다.

### 4.10 `core/order_executor.py`

역할: 실제 주문 제출, 주문 결과 기록, realized PnL 기록.

주요 로직:

- `submit_order()`가 수량, step size, min notional, 잔고 등을 검증한다.
- reduce-only 주문은 포지션 축소 목적이므로 수량을 키우지 않고 step rounding만 적용한다.
- 일반 신규 시장가 주문은 percent price preflight로 가격 필터 실패 가능성을 사전 차단한다.
- `get_current_price()`는 로컬 market data에 없으면 live ticker price로 fallback한다.
- `_process_order_result()`는 주문 결과를 `real_orders`에 남긴다.
- `reconcile_pending_reduce_only_fills()`는 `NEW/PARTIALLY_FILLED` reduce-only 주문을 거래소에 재조회한다.
- 거래소가 `FILLED`를 반환하면 `_apply_filled_reconciliation()`으로 가격, 체결수량, 상태, realized PnL을 보정한다.
- `_record_realized_pnl_event()`는 realized PnL journal과 symbol performance를 갱신한다.

판단:

- STEP27에서 6건의 누락 청산 체결을 복구했다.
- 이 로직은 향후 `NEW -> FILLED` 지연 확정 주문이 다시 발생해도 저널 누락을 줄인다.

### 4.11 `core/protective_order_manager.py`

역할: stop loss, take profit 보호 주문 배치와 취소.

주요 로직:

- `submit_protective_order()`가 `STOP_MARKET`, `TAKE_PROFIT_MARKET` 등 보호 주문을 제출한다.
- `_normalize_trigger_price()`와 `_round_price_to_tick()`이 tick size와 현재가 대비 유효한 트리거 가격을 보정한다.
- `get_open_orders()`로 심볼별 열린 주문을 조회한다.
- `cancel_symbol_protective_orders()`로 해당 심볼 보호 주문을 정리한다.

판단:

- STEP26 이후 포지션이 0이 되었고, 고아 미체결 주문도 0개로 정리됐다.

### 4.12 `core/position_manager.py`

역할: 포지션 상태 계산, 부분 청산, 전체 청산, exit 조건 관리.

주요 로직:

- `get_position_management_state()`가 진입가, 현재가, amount로 미실현 손익과 보유 시간을 계산한다.
- `close_partial_position()`은 reduce-only 주문으로 일부 수량을 닫는다.
- `close_position()`은 reduce-only 주문으로 전체 포지션을 닫는다.
- `manage_open_positions()`는 현재가 갱신, 부분익절, EMA21 trailing exit를 수행한다.
- funding close window 관련 보조 로직도 포함되어 있다.

판단:

- 현재 보유 포지션이 없으므로 exit 관리 대상도 없다.
- reduce-only 주문이 처음 `NEW`로 반환될 수 있으므로, 새 리컨실리에이션과 함께 동작하는 것이 중요하다.

### 4.13 `core/partial_take_profit_manager.py`

역할: 부분 익절 상태 관리.

주요 로직:

- `check_partial_take_profit()`가 TP 레벨 도달 여부를 확인한다.
- `_execute_partial_close()`가 부분 청산 요청을 만든다.
- `update_trailing_stop()`가 trailing stop 상태를 관리한다.

판단:

- STEP27에서 AKEUSDT 부분익절 3건이 누락 저널에서 복구됐다.

### 4.14 `core/pending_order_manager.py`

역할: pending 주문 후처리.

주요 로직:

- `refresh_pending_orders()`가 pending order 상태를 조회한다.
- `estimate_realized_pnl()`과 `_record_realized_pnl_event()`가 pending 주문 확정 시 저널을 기록한다.
- `recompute_trade_counters()`로 카운터를 재계산한다.

판단:

- 현재는 `OrderExecutor.reconcile_pending_reduce_only_fills()`가 reduce-only 청산의 누락 보정을 직접 담당한다.
- 두 경로가 중복 기록하지 않도록 `_record_realized_pnl_event()`는 order id 중복을 방지한다.

## 5. 오늘 진화 기록 요약

STEP18:

- 심볼 품질 필터 도입.
- `MYROUSDT`가 `flat_price_vs_sma`, `weak_trend_strength`, `very_low_volatility`로 문제 심볼 판정.

STEP19-24:

- `MYROUSDT` 청산 시도.
- 시장가 close가 가격 필터로 실패했고, reduce-only limit GTC fallback으로 최종 청산 완료.

STEP25:

- strict 품질 기준 강화.
- `HIPPOUSDT`, `REIUSDT` 청산.
- 당시 `NEIROUSDT`, `ZRCUSDT`는 약점 1개 보유 허용 때문에 남음.

STEP26:

- 보유 조건을 신규 진입과 대칭화.
- `NEIROUSDT`: `thin_recent_volume`으로 청산.
- `ZRCUSDT`: `weak_trend_strength`로 청산.
- 두 주문 모두 거래소 최종 상태 `FILLED`.
- 포지션 0개 확인.
- 남아 있던 BTCUSDT 일반 LIMIT BUY 고아 주문 2개 취소.
- 미체결 주문 0개 확인.

STEP27:

- reduce-only 체결 리컨실리에이션 추가.
- 누락된 6건을 거래소 조회로 `FILLED` 보정.
- realized PnL journal `21 -> 27` 복구.

복구된 6건:

- `AKEUSDT` partial TP 3건: `+0.0244404`, `+0.0489087`, `+0.0244683`
- `FUNUSDT` EMA21 trailing 1건: `+0.428992`
- `NEIROUSDT` strict quality close 1건: `-0.1973436`
- `ZRCUSDT` strict quality close 1건: `-0.24549`

## 6. 검증 결과

실행한 검증:

- 핵심 런타임 파일 `py_compile`: 통과
- 운영 도구 `py_compile`: 통과
- 런타임 초기화: 통과
- Binance demo futures 포지션 동기화: 통과
- Binance demo futures open orders 조회: 통과
- 최종 active positions: 0개
- 최종 open orders: 0개
- 최종 system errors: 0개

실행하지 못한 검증:

- `pytest`: `.venv`에 pytest가 설치되어 있지 않아 실행 불가

## 7. 남은 리스크와 권장 다음 단계

리스크 1: API 키가 config에 평문 저장됨.

- `config.json`에 testnet 키와 secret이 직접 들어 있다.
- 다음 단계에서 config 내 키 제거, `.env` 단일 사용, `.gitignore` 재확인이 필요하다.

리스크 2: `minimal_thresholds`가 매우 낮음.

- 현재 진입 방어는 품질 필터가 담당한다.
- 다음 진화에서는 confidence 최소값과 품질 필터 기준을 통합해 “진입 점수 하한”을 명확히 둘 필요가 있다.

리스크 3: 시장 데이터 후보군은 상위 50개까지 넓게 가져온다.

- 품질 필터가 강해졌으므로 즉시 위험은 줄었지만, 심볼 universe 단계에서도 `volume * price`, spread, tick size, min notional, 최근 체결 밀도까지 반영하면 더 안정적이다.

리스크 4: pytest 미설치.

- 자동화 회귀 검증을 하려면 `.venv`에 pytest를 설치하거나 프로젝트 의존성 설치를 정리해야 한다.

권장 다음 진화:

1. 키 보안 정리: `config.json`에서 API key/secret 제거.
2. 심볼 universe v2: 거래량 비율뿐 아니라 quote volume, 스프레드, tick size, 가격 하한, 최근 캔들 유효성으로 1차 차단.
3. 리컨실리에이션 자동 저장 보강: 런타임이 아닌 수동 운영 스크립트에서도 공통 저장 함수를 쓰게 정리.
4. pytest 환경 복구: 현재 핵심 py_compile는 통과했지만 자동 회귀 테스트는 도구 설치가 필요하다.

## 8. 최종 판단

현재 상태는 “실행 중단 후 안전 정리 완료” 상태다.

- 문제 심볼 보유 포지션은 모두 닫혔다.
- 고아 주문도 모두 정리됐다.
- 청산 체결 저널 누락도 복구됐다.
- 다음 실행을 시작할 수 있는 기반은 만들어졌다.

단, 다음 실거래 진화 전에 반드시 키 보안과 pytest 환경 복구를 먼저 처리하는 것이 좋다.
