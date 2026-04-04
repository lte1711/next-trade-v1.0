# Integrated Strategy Test Project

## Overview
이 프로젝트는 모든 테스트 전략을 하나의 통합된 프로그램으로 결합하여 실제 시장 상황을 정밀하게 테스트하기 위해 만들어졌습니다.

## Structure
```
integrated_strategy_test/
├── README.md                    # 프로젝트 설명
├── requirements.txt             # 의존성 패키지
├── config/                      # 설정 파일
│   ├── __init__.py
│   ├── settings.py              # 통합 설정
│   └── config.json              # 기본 설정 (원본과 호환)
├── src/                         # 소스 코드
│   ├── __init__.py
│   ├── main.py                  # 메인 실행 파일
│   ├── data/                    # 데이터 관리
│   │   ├── __init__.py
│   │   ├── market_data.py       # 실제 시장 데이터
│   │   └── data_loader.py       # 데이터 로더
│   ├── strategies/              # 전략 관리
│   │   ├── __init__.py
│   │   ├── base_strategy.py     # 기본 전략 클래스
│   │   ├── strategy_manager.py   # 전략 관리자
│   │   └── all_strategies.py    # 모든 전략 통합
│   ├── simulation/              # 시뮬레이션
│   │   ├── __init__.py
│   │   ├── engine.py            # 시뮬레이션 엔진
│   │   └── backtester.py       # 백테스터
│   ├── analysis/                # 분석
│   │   ├── __init__.py
│   │   ├── performance.py       # 성과 분석
│   │   └── reporter.py          # 보고서 생성
│   └── utils/                   # 유틸리티
│       ├── __init__.py
│       ├── helpers.py           # 헬퍼 함수
│       └── validators.py       # 데이터 검증
├── tests/                       # 테스트
│   ├── __init__.py
│   ├── test_strategies.py       # 전략 테스트
│   └── test_simulation.py       # 시뮬레이션 테스트
├── reports/                     # 보고서 저장
│   └── .gitkeep
├── logs/                        # 로그 저장
│   └── .gitkeep
└── integration/                  # 원본과의 통합 준비
    ├── __init__.py
    ├── compatibility.py         # 호환성 확인
    └── merger.py                # 통합 준비
```

## Features
- **29개 전략 통합**: 모든 테스트 전략을 하나의 프로그램으로 통합
- **실제 시장 데이터**: 실제 시장 상황을 정밀하게 반영
- **FACT 기반**: 모든 결과는 FACT만으로 기록
- **원본 호환성**: 원본 프로젝트와의 통합 준비
- **모듈화**: 각 기능을 모듈화하여 유지보수성 향상

## Usage
```bash
# 설치
pip install -r requirements.txt

# 실행
python src/main.py

# 테스트
python -m pytest tests/
```

## Integration with Original
- 원본 `config.json`과 호환성 유지
- 원본 API와의 통합 준비
- 원본 데이터 구조와의 호환성 확인
