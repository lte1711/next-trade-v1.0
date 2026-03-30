# NEXT-TRADE CONSTITUTION TESTING PROTOCOL v1.2.1

**제정일**: 2026-03-30  
**버전**: v1.2.1  
**상태**: ACTIVE  
**헌법 준수**: 필수

---

## 1. 테스트 환경 관리 원칙

### 1.1. 테스트 파일 격리
```text
TEST_ISOLATION_MANDATORY = YES
TEST_DIRECTORY_REQUIRED = YES
PROJECT_ROOT_CONTAMINATION_PROHIBITED = YES
```

### 1.2. 테스트 디렉토리 구조
```text
테스트 전용 디렉토리: C:\next-trade-ver1.0\tests\temp\
허용된 테스트 파일 생성 위치: tests\temp\ 내부만
금지된 테스트 파일 생성 위치: 프로젝트 루트 및 기타 디렉토리
```

---

## 2. 테스트 실행 프로토콜

### 2.1. 테스트 전 준비
```python
# 모든 테스트 스크립트는 아래 구조를 따라야 함
import os
from pathlib import Path

def setup_test_environment():
    """테스트 환경 설정"""
    test_dir = Path("tests/temp")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 테스트 작업 디렉토리로 이동
    os.chdir(test_dir)
    return test_dir

def cleanup_test_environment(test_dir):
    """테스트 환경 정리"""
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)
```

### 2.2. 테스트 파일 생성 규칙
```text
1. 모든 테스트 파일은 tests\temp\ 내부에만 생성
2. 파일명에는 "test_" 접두사 필수
3. 임시 파일은 ".tmp" 접미사 필수
4. 잠금 파일은 ".lock" 접미사 필수
5. 테스트 완료 후 즉시 정리 의무
```

### 2.3. 테스트 실행 의무사항
```text
BEFORE_TEST:
- tests\temp\ 디렉토리 생성 확인
- 기존 테스트 파일 정리
- 작업 디렉토리 이동

DURING_TEST:
- 모든 파일 생성을 tests\temp\ 내부로 제한
- 프로젝트 루트 오염 금지
- 임시 파일 누수 방지

AFTER_TEST:
- tests\temp\ 디렉토리 전체 삭제
- 프로젝트 루트 정리 확인
- 오염 파일 존재 여부 검증
```

---

## 3. 테스트 스크립트 표준

### 3.1. 필수 import 구조
```python
import os
import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def isolated_test_environment():
    """격리된 테스트 환경 컨텍스트"""
    original_dir = os.getcwd()
    test_dir = Path("tests/temp")
    
    try:
        # 테스트 환경 설정
        test_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(test_dir)
        yield test_dir
    finally:
        # 원래 디렉토리로 복귀
        os.chdir(original_dir)
        
        # 테스트 환경 정리
        if test_dir.exists():
            shutil.rmtree(test_dir)
```

### 3.2. 테스트 함수 템플릿
```python
def test_example():
    """테스트 예제"""
    with isolated_test_environment() as test_dir:
        # 테스트 로직 (test_dir 내부에서만 파일 생성)
        test_file = test_dir / "test_example.json"
        
        # 테스트 실행
        # ... 테스트 코드 ...
        
        # 자동 정리 (컨텍스트 종료 시)
        pass  # 명시적 정리 불필요
```

---

## 4. 금지 사항

### 4.1. 절대 금지 행위
```text
1. 프로젝트 루트에 테스트 파일 직접 생성
2. tests\temp\ 외부에 임시 파일 생성
3. 테스트 종료 후 파일 남기기
4. .lock 파일을 프로젝트 루트에 생성
5. 임시 파일 누수 방치
```

### 4.2. 제재 규정
```text
1차 위반: 테스트 결과 무효 및 재실행 요구
2차 위반: 테스트 권한 일시 정지
3차 위반: 테스트 실행 권한 영구 박탈
```

---

## 5. 검증 및 감사

### 5.1. 자동 검증
```python
def verify_test_cleanup():
    """테스트 정리 검증"""
    project_root = Path(".")
    
    # 금지된 파일 존재 검증
    forbidden_patterns = [
        "*.lock",
        "test_*.json",
        "tmp*.tmp",
        "perf_test_*"
    ]
    
    violations = []
    for pattern in forbidden_patterns:
        violations.extend(project_root.glob(pattern))
    
    # tests\temp\ 외부 파일 검증
    for file_path in violations:
        if not str(file_path).startswith("tests/temp/"):
            raise RuntimeError(f"Test contamination detected: {file_path}")
    
    return len(violations) == 0
```

### 5.2. 수동 감사 체크리스트
```text
□ 테스트 실행 전 tests\temp\ 존재 확인
□ 모든 테스트 파일이 tests\temp\ 내부에 생성됨
□ 테스트 완료 후 tests\temp\ 삭제 확인
□ 프로젝트 루트에 테스트 관련 파일 없음 확인
□ 잠금 파일 누수 없음 확인
```

---

## 6. 예외 처리

### 6.1. 허용된 예외
```text
1. tools/validation\ 내부의 통제된 테스트 파일
2. logs\ 내부의 운영 로그 파일
3. .venv\ 내부의 가상환경 파일
4. .git\ 내부의 버전 관리 파일
```

### 6.2. 예외 신청 절차
```text
1. 예외 필요 사유 명시
2. BAEKSEOL 총괄 승인 요청
3. 헌법 개정 프로세스 진행
4. 승인 후 예외 적용
```

---

## 7. 책임 및 의무

### 7.1. 테스트 실행자 의무
```text
- 테스트 프로토콜 준수 의무
- 환경 격리 보장 의무
- 사후 정리 완료 의무
- 오염 방지 보고 의무
```

### 7.2. 감시자 역할
```text
CANDY: 테스트 환경 준수 검증
GEMINI: 기술적 프로토콜 준수 확인
BAEKSEOL: 프로토콜 위반 시 제재
DENNIS: 최준 승인 및 예외 승인
```

---

## 8. 개정 이력

### v1.2.1 (2026-03-30)
- 테스트 환경 격리 의무화
- 프로젝트 루트 오염 금지
- 자동 정리 프로토콜 추가
- 제재 규정 명시

---

## 9. 발효

### [FACT]
```text
CONSTITUTION_STATUS = ACTIVE
CONSTITUTION_VERSION = v1.2.1
EFFECTIVE_DATE = 2026-03-30
COMPLIANCE_MANDATORY = YES
ENFORCEMENT_ACTIVE = YES
```

### [FACT] 적용 범위
```text
- 모든 테스트 스크립트
- 모든 테스트 실행 프로세스
- 모든 개발자 및 테스터
- 모든 자동화 테스트 시스템
```

---

## 10. 서명

**제정자**: BAEKSEOL (총괄)  
**승인자**: DENNIS (최종 승인)  
**감시자**: CANDY (data_validation), GEMINI (technical_verification)  
**실행자**: CODEX (execution)

---

**헌법 v1.2.1 준수**: 모든 테스트는 격리된 환경에서 실행되어야 함  
**위반 시 제재**: 테스트 결과 무효 및 권한 제한  
**준수 의무**: 모든 테스트 실행자는 본 프로토콜을 숙지하고 준수해야 함
