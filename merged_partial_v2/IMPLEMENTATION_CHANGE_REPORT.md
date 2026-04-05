# Merged Partial V2 수정 및 설치본 종합 보고서

## 1. 개요

이 보고서는 `merged_partial_v2` 합본 프로젝트에 대해 지금까지 진행한 주요 수정 사항, 관련 파일, 설치본 구성, 설치 및 실행 검증 결과를 정리한 문서다.

대상 경로:
- 소스 루트: `C:\next-trade-ver1.0\merged_partial_v2`
- 설치 파일: `C:\trade\install.exe`
- 설치 폴더: `C:\tradev1`

## 2. 주요 목표

이번 작업에서 달성하려고 한 핵심 목표는 다음과 같다.

1. 원본 프로젝트 의존도 없이 동작하는 설치본 구성
2. 직접 `exe` 실행 시 콘솔/PowerShell 창 없이 백그라운드 실행
3. 대시보드 관리창 제공
4. 자동매매/자동운용 루프와 관리창의 연동
5. 설치본에서 실시간 또는 준실시간 상태 확인 가능 구조 확보
6. 설치/재설치/삭제 과정의 반복 안정성 확보

## 3. 핵심 수정 사항

### 3.1 패키징 및 설치 구조 수정

#### 목적
- 설치본이 원본 폴더 없이 독립 실행되게 구성
- 설치 시 필요한 모든 실행 파일, 리소스, 설정, 대시보드 자산을 함께 포함

#### 수정 파일
- `C:\next-trade-ver1.0\merged_partial_v2\merged_partial_v2_v1.spec`
- `C:\next-trade-ver1.0\merged_partial_v2\build_v1.ps1`
- `C:\next-trade-ver1.0\merged_partial_v2\create_install_exe.ps1`
- `C:\next-trade-ver1.0\merged_partial_v2\package_v1.ps1`
- `C:\next-trade-ver1.0\merged_partial_v2\installer_assets\install_from_package.py`

#### 반영 내용
- 설치본에 `config`, `profile_reports`, `dashboard_assets`, `.env.merged_partial_v2` 포함
- `install.exe` 단독으로 `C:\tradev1` 설치 가능 구조 구성
- 설치 후 바탕화면 및 시작 메뉴 바로가기 생성
- 설치 폴더 기준 상대 경로가 아닌 실행 파일 기준 경로 사용

### 3.2 직접 exe 실행 시 콘솔 제거

#### 목적
- `C:\tradev1\merged_partial_v2_v1.exe` 직접 실행 시 콘솔창/PowerShell 창 노출 제거

#### 수정 파일
- `C:\next-trade-ver1.0\merged_partial_v2\merged_partial_v2_v1.spec`

#### 반영 내용
- PyInstaller `console=True`에서 `console=False`로 변경
- 부트로더가 `run.exe`가 아니라 `runw.exe`를 사용하도록 빌드

### 3.3 백그라운드 실행 런처 추가

#### 목적
- 사용자가 바로가기를 눌렀을 때 숨김 실행되도록 구성

#### 수정 파일
- `C:\next-trade-ver1.0\merged_partial_v2\build_v1.ps1`
- `C:\next-trade-ver1.0\merged_partial_v2\installer_assets\install_from_package.py`

#### 생성 파일
- `C:\tradev1\Launch Merged Partial V2 v1.vbs`
- `C:\tradev1\Open Merged Partial V2 Dashboard.vbs`

#### 반영 내용
- 앱 실행 바로가기와 대시보드 실행 바로가기가 모두 `vbs` 숨김 실행기를 사용
- 콘솔창 없이 백그라운드 실행 가능

### 3.4 대시보드 1차~3차 및 직관성 개선

#### 목적
- 상태 조회, 추천, 자동운용, 주문 상태를 한 화면에서 보기 쉽게 제공

#### 수정 파일
- `C:\next-trade-ver1.0\merged_partial_v2\dashboard_assets\index.html`
- `C:\next-trade-ver1.0\merged_partial_v2\dashboard_assets\app.js`
- `C:\next-trade-ver1.0\merged_partial_v2\dashboard_assets\styles.css`
- `C:\next-trade-ver1.0\merged_partial_v2\src\merged_partial_v2\dashboard_server.py`
- `C:\next-trade-ver1.0\merged_partial_v2\src\merged_partial_v2\services\process_manager_service.py`

#### 반영 내용
- 관리창 한글화
- 카드형 대시보드 구성
- 주요 카드:
  - 진행 상태
  - 실행 상태
  - 시장 상태
  - 최근 실행
  - 자동매매 사이클
  - 자금 요약
  - 의사결정 상태
  - 최우선 추천
  - 실행 결과
  - 투자 종목
  - 리스크 게이트
- `Dry Run / Live` 토글 추가
- `새로고침`, `드라이런 시작`, `라이브 시작`, `자동 중지`, `헬스체크`, `추천 실행`, `전체 청산 및 중지` 버튼 추가

### 3.5 자금 활용 전략 개편

#### 목적
- 소액 고정 투자 구조에서 계정 전체 자금 활용 구조로 전환

#### 수정 파일
- `C:\next-trade-ver1.0\merged_partial_v2\src\merged_partial_v2\services\paper_decision_service.py`
- `C:\next-trade-ver1.0\merged_partial_v2\src\merged_partial_v2\services\autonomous_trading_service.py`
- `C:\next-trade-ver1.0\merged_partial_v2\src\merged_partial_v2\services\autonomous_state_service.py`
- `C:\next-trade-ver1.0\merged_partial_v2\src\merged_partial_v2\services\profile_switcher_service.py`
- `C:\next-trade-ver1.0\integrated_strategy_test\src\modules\portfolio_manager.py`
- `C:\next-trade-ver1.0\integrated_strategy_test\src\modules\simulator.py`

#### 반영 내용
- `fixed_allocation` 중심 구조 제거
- `target_invested_capital` 및 `target_allocation_per_symbol` 기반 배분 구조 도입
- 신규 진입뿐 아니라 `scale_in` 허용
- 선택 종목 수 기준 전체 자금 목표 배분

### 3.6 주문 실행 및 거래소 규칙 대응 보강

#### 목적
- 자동매매 시 수량 정밀도, 최소 주문 금액, step size 문제로 인한 주문 실패 방지

#### 수정 파일
- `C:\next-trade-ver1.0\merged_partial_v2\src\merged_partial_v2\exchange\local_binance_bridge.py`
- `C:\next-trade-ver1.0\merged_partial_v2\src\merged_partial_v2\exchange\execution_client.py`

#### 반영 내용
- `exchangeInfo` 기반 심볼별 규칙 적용
- `quantityPrecision`, `stepSize`, `minQty`, `minNotional` 보정
- 주문 후 체결 polling
- 주문 실패 카테고리 분류 및 로그 기록
- `open_and_close_test_order()` 헬퍼 추가

### 3.7 리스크 게이트 및 자동운용 보강

#### 목적
- 계정 조회 실패, 주문 실패, 비정상 상태에서 자동 진입 차단

#### 수정 파일
- `C:\next-trade-ver1.0\merged_partial_v2\src\merged_partial_v2\services\risk_gate_service.py`
- `C:\next-trade-ver1.0\merged_partial_v2\src\merged_partial_v2\simulation\strategy_engine.py`
- `C:\next-trade-ver1.0\merged_partial_v2\src\merged_partial_v2\main.py`

#### 반영 내용
- `recent_health_check`, `recent_order_failures` 기반 차단
- `paper_decision.risk_gate` 요약 제공
- `merged_snapshot.json`에 운영 판단 결과 기록

### 3.8 설치본 기본 동작 변경

#### 목적
- 설치본 직접 실행 시 대시보드가 함께 올라오도록 개선

#### 수정 파일
- `C:\next-trade-ver1.0\merged_partial_v2\run_merged_partial_v2.py`

#### 반영 내용
- 설치본 `no-arg` 실행 시:
  - 대시보드 자동 시작 시도
  - 설치 환경 기본 동작 실행
- 설치본 `--dashboard` 실행 경로 추가
- 예외 발생 시 로그를 남기기 위한 crash log 코드 추가

### 3.9 상태 API 성능 및 안정성 조정

#### 목적
- 대시보드가 무한로딩 없이 즉시 열리도록 개선

#### 수정 파일
- `C:\next-trade-ver1.0\merged_partial_v2\src\merged_partial_v2\dashboard_server.py`
- `C:\next-trade-ver1.0\merged_partial_v2\dashboard_assets\app.js`

#### 반영 내용
- `/api/status`를 초경량 경로로 조정
- `/api/status/refresh`는 강제 갱신용 유지
- 프론트는 3초 주기 갱신
- `refreshInFlight` 추가로 중첩 요청 방지

## 4. 관리창 표시 항목 재구성

사용자 요청에 따라 관리창에는 다음 항목들이 들어가도록 정리했다.

### 자금 요약
- 총자금
- 투자금
- 잔여금
- 현재 수익금
- 수익율
- 투자종목
- 상승확율
- 실재확율

### 포지션 표
- 종목
- 투자금
- 진입가
- 현재가
- 수익금
- 수익율
- 상승확율
- 실재확율

## 5. 설치본 및 배포본 구성

### 배포 파일
- `C:\trade\install.exe`

### 설치 결과 폴더
- `C:\tradev1`

### 설치 후 주요 파일
- `C:\tradev1\merged_partial_v2_v1.exe`
- `C:\tradev1\.env.merged_partial_v2`
- `C:\tradev1\Launch Merged Partial V2 v1.vbs`
- `C:\tradev1\Open Merged Partial V2 Dashboard.vbs`
- `C:\tradev1\_internal\dashboard_assets\index.html`
- `C:\tradev1\_internal\dashboard_assets\app.js`
- `C:\tradev1\_internal\dashboard_assets\styles.css`

## 6. 설치본 검증 이력 요약

### 확인된 정상 동작
- 설치본 `exe` 직접 실행 시 콘솔창 미표시
- `vbs` 바로가기 기준 백그라운드 실행
- 설치 경로 `C:\tradev1` 고정 설치
- 대시보드 포트 `8787` 사용
- `api/process` 응답 확인

### 발견된 문제와 해결
1. `PowerShell` 창 노출
   - 원인: 콘솔 빌드 및 배치 실행
   - 해결: `runw.exe` 기반 빌드 + `vbs` 숨김 런처

2. 관리창 한글 깨짐
   - 원인: 설치본 자산과 소스 자산 불일치 및 깨진 문자열
   - 해결: `index.html`, `app.js` 전면 재작성 및 재반영

3. `127.0.0.1:8787` 연결 거부
   - 원인: 대시보드 서버 미기동 또는 설치본 경로 문제
   - 해결: 설치본 대시보드 자동 시작 로직 추가 및 재설치

4. 상태 화면 무한로딩
   - 원인: `/api/status` 응답 경로가 무겁고 느림
   - 해결: 경량 상태 응답 경로 도입

5. 설치 폴더 삭제/재설치 실패
   - 원인: 설치본 프로세스가 폴더 잠금
   - 해결: 관련 프로세스 종료 후 재설치

## 7. 현재 확인된 운영 상태

현재 기준으로 확인된 점:
- 설치본은 최신으로 다시 생성됨
- 배포 파일은 `C:\trade\install.exe`
- 설치 폴더는 `C:\tradev1`
- 대시보드 포트는 `8787`

단, 설치본은 반복적으로 재설치/재기동을 거치며 검증 중이었고, 마지막 단계에서는 `api/status` 안정화와 설치본 대시보드 응답 정상화를 중심으로 추가 점검을 진행했다.

## 8. 남아 있는 점검 포인트

다음 항목은 최종 배포 전 한 번 더 확인하는 것이 좋다.

1. 설치 직후 `C:\tradev1\merged_partial_v2_v1.exe --dashboard --dashboard-port 8787` 단독 응답 검증
2. `api/status`가 즉시 열리고 카드가 실제 데이터로 채워지는지 브라우저 확인
3. `라이브 시작` 전 `드라이런 시작`으로 자동운용 상태 반영 확인
4. `추천 실행`, `전체 청산 및 중지` 버튼이 실제 상태 파일과 동기화되는지 확인

## 9. 결론

이번 작업으로 `merged_partial_v2`는 다음 수준까지 올라왔다.

- 원본 프로젝트 없이 설치 가능한 독립 설치본
- 직접 exe 실행 시 콘솔창이 없는 실행 구조
- 백그라운드 실행용 바로가기 제공
- 한글 관리창 제공
- 자동운용, 헬스체크, 추천 실행, 전체 정리 기능 제공
- 전체 자금 활용 전략 구조로 전환
- 설치/삭제/재설치가 가능한 배포본 유지

현재 가장 중요한 남은 과제는 설치본 기준 대시보드 응답 안정성을 최종적으로 완전히 고정하는 것이다. 이 부분은 최근 수정으로 상당 부분 정리됐고, 설치본 기준 마지막 동작 확인만 추가로 마치면 된다.
