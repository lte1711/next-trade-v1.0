# NEXT-TRADE V1 운영자 장애 대응 매뉴얼

## 🎯 개요
본 매뉴얼은 NEXT-TRADE V1 운영 중 발생할 수 있는 장애 상황별 대응 절차를 안내합니다.

---

## 🚨 1. 긴급 장애 대응

### 1.1 시스템 전체 장애
#### 증상
- 프로그램이 전체적으로 응답 없음
- 대시보드 접속 불가
- 모든 기능 작동 중지

#### 즉시 조치
1. **프로세스 확인**
   ```powershell
   Get-Process | Where-Object {$_.ProcessName -like "*merged*"}
   ```

2. **강제 종료**
   ```powershell
   Stop-Process -Name "merged_partial_v2_v1" -Force
   ```

3. **로그 확인**
   - `C:\tradev1\order_logs\` 폴더 확인
   - 최근 오류 메시지 확인

4. **재시작**
   - "Launch Merged Partial V2 v1" 바로가기 실행
   - 또는 `C:\tradev1\merged_partial_v2_v1.exe` 직접 실행

### 1.2 대시보드 접속 장애
#### 증상
- 브라우저에서 `http://127.0.0.1:8787` 접속 불가
- "연결할 수 없음" 오류
- 무한 로딩 상태

#### 대응 절차
1. **포트 확인**
   ```powershell
   netstat -ano | findstr :8787
   ```

2. **프로세스 상태 확인**
   ```powershell
   Get-Process | Where-Object {$_.ProcessName -like "*merged*"}
   ```

3. **방화벽 확인**
   - Windows 방화벽 → 고급 설정 → 인바운드 규칙
   - 포트 8787 허용 규칙 확인

4. **서비스 재시작**
   - 프로그램 완전 종료
   - 30초 대기 후 재시작

### 1.3 API 연동 장애
#### 증상
- "API 연결 실패" 메시지
- 시장 데이터 수신 안됨
- 자동거래 작동 안됨

#### 대응 절차
1. **네트워크 연결 확인**
   ```powershell
   ping api.binance.com
   Test-NetConnection api.binance.com -Port 443
   ```

2. **API 키 유효성 확인**
   - `.env.merged_partial_v2` 파일 확인
   - API 키 만료일 확인

3. **거래소 상태 확인**
   - 바이낸스 공식 사이트 접속
   - 서비스 상태 페이지 확인

4. **백업 모드 전환**
   - Dry Run 모드로 전환
   - Fallback 데이터 사용 확인

---

## ⚠️ 2. 경고 장애 대응

### 2.1 성능 저하
#### 증상
- 대시보드 로딩 지연 (10초 이상)
- API 응답 시간 증가 (5초 이상)
- 시스템 리소스 사용량 증가

#### 진단 절차
1. **시스템 리소스 확인**
   ```powershell
   Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2
   Get-Counter '\Memory\Available MBytes'
   Get-Counter '\Process(*)\Working Set'
   ```

2. **디스크 공간 확인**
   ```powershell
   Get-PSDrive C
   ```

3. **네트워크 대역폭 확인**
   - 속도 테스트 사이트 접속
   - 네트워크 사용량 모니터링

#### 최적화 조치
1. **불필요 프로세스 종료**
2. **디스크 정리**
3. **프로그램 재시작**
4. **캐시 정리**

### 2.2 데이터 불일치
#### 증상
- 대시보드 표시 데이터 불일치
- 자금 정보 오차 발생
- 포지션 정보 누락

#### 대응 절차
1. **스냅샷 파일 확인**
   - `C:\tradev1\merged_snapshot.json`
   - 파일 무결성 확인

2. **데이터 동기화**
   - "새로고침" 버튼 클릭
   - 강제 동기화 실행

3. **API 재연결**
   - 프로그램 재시작
   - API 연결 재설정

### 2.3 자동거래 오류
#### 증상
- 자동거래 주기적 실패
- 주문 실행 오류 발생
- 포지션 관리 오류

#### 대응 절차
1. **오류 로그 분석**
   - `order_logs\` 폴더 확인
   - 오류 유형별 분류

2. **거래소 규칙 확인**
   - 최소 주문 금액
   - 수량 정밀도
   - step size

3. **리스크 게이트 확인**
   - 계정 상태 확인
   - 잔고 부족 여부
   - 거래 제한 여부

---

## 🔧 3. 예방적 조치

### 3.1 정기 모니터링
#### 일일 점검
- [ ] 프로그램 실행 상태 확인
- [ ] 대시보드 접속 테스트
- [ ] API 연결 상태 확인
- [ ] 로그 파일 확인

#### 주간 점검
- [ ] 시스템 성능 벤치마크
- [ ] 디스크 공간 확인
- [ ] 백업 파일 확인
- [ ] 네트워크 상태 점검

### 3.2 백업 및 복구
#### 백업 대상
1. **설정 파일**
   - `.env.merged_partial_v2`
   - `config.json`

2. **데이터 파일**
   - `merged_snapshot.json`
   - `execution_reports\`
   - `autonomous_reports\`

3. **로그 파일**
   - `order_logs\`

#### 백업 절차
1. **정기 백업**
   ```powershell
   $backupPath = "C:\tradev1\backup\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
   New-Item -ItemType Directory -Path $backupPath -Force
   Copy-Item "C:\tradev1\.env.merged_partial_v2" $backupPath
   Copy-Item "C:\tradev1\merged_snapshot.json" $backupPath
   Copy-Item "C:\tradev1\execution_reports" $backupPath -Recurse
   ```

2. **자동 백업 스크립트**
   ```powershell
   # backup_schedule.ps1
   $source = "C:\tradev1"
   $destination = "D:\trade_backup"
   robocopy $source $destination /MIR /R:2 /W:1
   ```

#### 복구 절차
1. **설정 복구**
   - 백업 파일에서 설정 복사
   - 프로그램 재시작

2. **데이터 복구**
   - 스냅샷 파일 복구
   - 상태 동기화

### 3.3 보안 강화
#### 접근 제어
- [ ] 관리자 권한만 실행 가능
- [ ] 설정 파일 접근 제한
- [ ] 로그 파일 무결성 확인

#### 모니터링
- [ ] 비정상 접속 시도 감지
- [ ] 데이터 위변조 감지
- [ ] 시스템 리소스 이상 사용 감지

---

## 📊 4. 모니터링 도구

### 4.1 시스템 모니터링
#### 성능 모니터링
```powershell
# performance_monitor.ps1
while ($true) {
    $cpu = Get-Counter '\Processor(_Total)\% Processor Time'
    $memory = Get-Counter '\Memory\Available MBytes'
    $disk = Get-Counter '\PhysicalDisk(_Total)\% Disk Time'
    
    Write-Host "CPU: $($cpu.CounterSamples.CookedValue)% Memory: $($memory.CounterSamples.CookedValue)MB Disk: $($disk.CounterSamples.CookedValue)%"
    Start-Sleep 60
}
```

#### 로그 모니터링
```powershell
# log_monitor.ps1
Get-Content "C:\tradev1\order_logs\*.log" -Tail 10 -Wait | ForEach-Object {
    if ($_ -match "ERROR|CRITICAL|FAIL") {
        Write-Host "ALERT: $_" -ForegroundColor Red
    }
}
```

### 4.2 네트워크 모니터링
#### 연결 상태 확인
```powershell
# network_monitor.ps1
while ($true) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8787/api/status" -TimeoutSec 5
        Write-Host "API Status: OK"
    } catch {
        Write-Host "API Status: FAILED - $($_.Exception.Message)"
    }
    Start-Sleep 30
}
```

---

## 🚨 5. 비상 연락망

### 5.1 심각도 분류
#### 레벨 1 (치명적)
- 시스템 전체 장애
- 데이터 손실 위험
- 금전적 손실 발생

#### 레벨 2 (심각)
- 주요 기능 장애
- 서비스 품질 저하
- 사용자 영향 큼

#### 레벨 3 (경고)
- 부분 기능 장애
- 성능 저하
- 사용자 불편 발생

### 5.2 연락 체계
#### 즉시 연락
- **기술 책임자**: [연락처]
- **시스템 관리자**: [연락처]
- **개발팀**: [연락처]

#### 대응팀
- **1차 대응**: 운영팀
- **2차 대응**: 개발팀
- **3차 대응**: 경영진

---

## 📋 6. 장애 보고서

### 6.1 보고서 양식
```
# 장애 보고서

## 기본 정보
- 발생일시: 
- 보고자: 
- 심각도: 
- 영향 시스템: 

## 증상
- 현재 증상: 
- 발생 빈도: 
- 영향 범위: 

## 원인 분석
- 직접 원인: 
- 근본 원인: 
- 관련 요소: 

## 조치 내용
- 즉시 조치: 
- 근본 조치: 
- 예방 조치: 

## 결과
- 조치 시간: 
- 복구 시간: 
- 영향 기간: 
- 재발 방지: 
```

### 6.2 장애 통계
#### 월간 장애 현황
| 월 | 레벨1 | 레벨2 | 레벨3 | 평균 복구시간 |
|----|--------|--------|--------|--------------|
| 1월 |        |        |        |              |
| 2월 |        |        |        |              |

#### 장애 유형별 분석
| 유형 | 발생 횟수 | 평균 처리시간 | 재발률 |
|------|------------|--------------|----------|
| 시스템 장애 |            |              |          |
| 네트워크 장애 |            |              |          |
| API 연동 장애 |            |              |          |
| 데이터 장애 |            |              |          |

---

## 🎯 7. 복구 계획

### 7.1 RTO/RPO 목표
- **RTO (복구 시간 목표)**: 30분 이내
- **RPO (복구 시점 목표)**: 5분 이내 데이터 손실 방지

### 7.2 복구 우선순위
1. **1순위**: 핵심 기능 복구 (API 연동, 자동거래)
2. **2순위**: 모니터링 기능 복구 (대시보드, 로깅)
3. **3순위**: 부가 기능 복구 (보고서, 분석)

### 7.3 테스트 계획
- [ ] 복구 후 기능 테스트
- [ ] 데이터 무결성 검증
- [ ] 성능 벤치마크
- [ ] 사용자 접속 테스트

---

## 📝 8. 개선 방안

### 8.1 장애 예방
- [ ] 시스템 리소스 모니터링 강화
- [ ] 이중화 구축 검토
- [ ] 자동 복구 시스템 구축
- [ ] 장애 예측 시스템 도입

### 8.2 대응 능력 향상
- [ ] 장애 대응 매뉴얼 주기적 개선
- [ ] 스태프 교육 및 시뮬레이션
- [ ] 외부 전문가와 협력 체계 구축
- [ ] 24/7 모니터링 시스템 구축

---

**본 매뉴얼은 NEXT-TRADE V1의 안정적인 운영을 위한 지침입니다. 모든 장애 상황에 신속하고 정확하게 대응할 수 있도록 정기적인 검토와 훈련이 필요합니다.**

**버전**: v1.0.0  
**최종 업데이트**: 2026-04-05  
**담당자**: 운영팀
