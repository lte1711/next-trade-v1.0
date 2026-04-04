# 모듈화 프로그램 실제 실행 플로우

## 실제 플로우차트

```text
프로그램 시작
|
+-- main_modular.main()
    |
    +-- ModularTradingSimulator 생성
    |
    +-- run_simulation(30분, 3분 주기)
        |
        +-- [초기 스캔]
        |   +-- 거래량 상위 80개 심볼 조회
        |   +-- bullish_score 계산
        |   +-- market_regime 기준 profit_potential 평가
        |
        +-- 기준 충족 심볼 존재?
        |   |
        |   +-- 예
        |   |   +-- 심볼 선택
        |   |   +-- 포트폴리오 초기화
        |   |   +-- 메인 루프 진입
        |   |
        |   +-- 아니오
        |       +-- _continuous_market_analysis() 진입
        |           |
        |           +-- 남은 시간 동안 3분 주기 반복
        |           |   +-- market_regime 계산
        |           |   +-- 거래량 상위 80개 재조회
        |           |   +-- bullish_score 재계산
        |           |   +-- profit_potential 재평가
        |           |
        |           +-- 진입 가능 심볼 발견?
        |               |
        |               +-- 예 -> 즉시 포트폴리오 초기화 후 메인 루프 전환
        |               +-- 아니오 -> 다음 주기 대기
        |
        +-- [메인 루프]
            +-- market_regime 재계산
            +-- 보유 심볼 실시간 가격 갱신
            +-- 손익/순자산 계산
            +-- 리밸런싱 평가
            |   +-- 손실 임계값 이하 또는 기대치 기준 미달 심볼 제거
            |   +-- 기준 충족 신규 심볼 추가
            +-- 다음 주기까지 대기
            +-- 종료 시 최종 보고서 생성
```

## 리밸런싱 실제 판단 규칙

```text
보유 심볼별로:
|
+-- 실시간 가격, RSI, MACD, bullish_score 조회
|
+-- 현재 pnl_percent 계산
|
+-- pnl_percent <= replacement_threshold ?
|   +-- 예 -> 제거 후보
|   +-- 아니오 -> 다음 판단
|
+-- profit_potential < 현재 market_regime threshold ?
    +-- 예 -> 제거 후보
    +-- 아니오 -> 유지

이후:
|
+-- 거래량 상위 심볼을 실시간 지표로 재평가
+-- threshold 이상 신규 심볼 탐색
+-- 포트폴리오 여유 슬롯과 현금 범위 내에서 추가
```

## 시장 상태 분류 규칙

```text
거래량 상위 20개 심볼의 절대 24시간 등락률 평균 계산
|
+-- 평균 > 5.0 -> EXTREME
+-- 평균 > 2.5 -> HIGH_VOLATILITY
+-- 그 외 -> NORMAL
```

## 임계값 테이블

| 시장 상태 | 진입/유지 기준 | 최대 심볼 수 |
|---|---:|---:|
| `EXTREME` | 70 | 5 |
| `HIGH_VOLATILITY` | 75 | 7 |
| `NORMAL` | 80 | 10 |
