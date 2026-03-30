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

### [FACT] 현재 로그 파일 목록 확인
<tool_call>list_dir
<arg_key>DirectoryPath</arg_key>
<arg_value>c:\next-trade-ver1.0\logs
