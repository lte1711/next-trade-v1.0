# 테스트 멀티 전략 보고서
생성 시간: 2026-04-02T10:56:07.257762+00:00

## 테스트 결과
### volatility_breakout_v1
- 성공 여부: True
- 신호: HOLD
- 신호 점수: 0.0
- 확신도: 0.0

### mean_reversion_v1
- 성공 여부: True
- 신호: SHORT
- 신호 점수: 7.062574517465234
- 확신도: 0.7062574517465234

## 원본 프로젝트와의 비교
### 새로운 전략 상태
- volatility_breakout_v1: 미포함
- mean_reversion_v1: 미포함
### 기존 전략 상태
- momentum_intraday_v1: 포함됨
- trend_following_v1: 포함됨
### 통합 이슈
- volatility_breakout_v1 전략이 원본 프로젝트에 없음
- mean_reversion_v1 전략이 원본 프로젝트에 없음
### 권장 사항
- 2개 전략을 원본 프로젝트에 합체 필요