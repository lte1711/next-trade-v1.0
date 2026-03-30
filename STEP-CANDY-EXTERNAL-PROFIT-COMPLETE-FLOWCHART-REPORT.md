# 외부 수익성 전략 전체 플로우차트 보고서

**작성자**: CANDY (data_validation + execution)  
**헌법**: NEXT-TRADE v1.2.1  
**상태**: COMPLETE  
**기준**: FACT ONLY

---

## 1. 전체 워크플로우 차트

### [FACT] 현재 워크플로우 상태
```text
수정 전 표준: BAEKSEOL -> CODEX -> CANDY -> GEMINI -> DENNIS
현재 예외 적용: BAEKSEOL -> CANDY -> GEMINI -> DENNIS
```

### [FACT] 전체 프로세스 맵
```mermaid
graph TD
    A[BAEKSEOL 설계] --> B[CANDY 데이터 진단]
    B --> C[CANDY MVP 구현]
    C --> D[GEMINI 기술 검토]
    D --> E[DENNIS 최종 승인]
    
    A1[외부 전략 설계] --> B1[데이터 소스 확정]
    B1 --> C1[외부 모듈 구현]
    C1 --> D1[기술적 타당성 검토]
    D1 --> E1[최종 승인 결정]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#fce4ec
```

---

## 2. 상세 모듈 플로우차트

### [FACT] 외부 전략 모듈 아키텍처
```mermaid
graph TB
    subgraph "기존 엔진 (수정 금지)"
        E1[profitmax_v1_runner.py]
        E2[multi5_engine_runtime.py]
        E3[strategy_signals/*.json]
    end
    
    subgraph "외부 전략 모듈 (MVP)"
        M1[market_filter_module.py]
        M2[signal_quality_gate.py]
        M3[start_external_profit_strategy.ps1]
    end
    
    subgraph "데이터 소스 (읽기 전용)"
        D1[portfolio_metrics_snapshot.json]
        D2[strategy_performance.json]
        D3[runtime_health_summary.json]
    end
    
    subgraph "출력 결과"
        O1[market_filter_status.json]
        O2[external_gate_decisions.jsonl]
        O3[strategy_signals_filtered/*.json]
    end
    
    D1 --> M1
    D2 --> M2
    D3 --> M1
    E3 --> M2
    
    M1 --> O1
    M2 --> O2
    M2 --> O3
    
    M3 --> M1
    M3 --> M2
    
    style E1 fill:#ffebee
    style E2 fill:#ffebee
    style E3 fill:#ffebee
    style M1 fill:#e8f5e8
    style M2 fill:#e8f5e8
    style M3 fill:#e8f5e8
```

---

## 3. 데이터 흐름 플로우차트

### [FACT] Market Filter Module 데이터 흐름
```mermaid
flowchart LR
    A[portfolio_metrics_snapshot.json] --> B[load_portfolio_metrics]
    C[runtime_health_summary.json] --> D[load_runtime_health]
    
    B --> E[evaluate_market_conditions]
    D --> E
    
    E --> F{Global Allow?}
    
    F -->|YES| G[ALLOW - Continue]
    F -->|NO| H[BLOCK - Stop]
    
    E --> I[save_market_filter_status]
    I --> J[market_filter_status.json]
    
    style A fill:#e3f2fd
    style C fill:#e3f2fd
    style J fill:#c8e6c9
    style G fill:#ffeb3b
    style H fill:#f44336
```

### [FACT] Signal Quality Gate Module 데이터 흐름
```mermaid
flowchart LR
    A[strategy_performance.json] --> B[load_strategy_performance]
    C[strategy_signals/*.json] --> D[load_strategy_signals]
    
    B --> E[evaluate_signal_quality]
    D --> E
    
    E --> F{Quality Check}
    
    F -->|PASS| G[Allow Signal]
    F -->|FAIL| H[Block Signal]
    
    G --> I[save_filtered_signals]
    H --> I
    
    E --> J[save_gate_decisions]
    J --> K[external_gate_decisions.jsonl]
    I --> L[strategy_signals_filtered/*.json]
    
    style A fill:#e3f2fd
    style C fill:#e3f2fd
    style L fill:#c8e6c9
    style K fill:#c8e6c9
    style G fill:#4caf50
    style H fill:#f44336
```

---

## 4. 실행 순서 플로우차트

### [FACT] Bootstrap PowerShell 실행 순서
```mermaid
sequenceDiagram
    participant PS as PowerShell Bootstrap
    participant MF as Market Filter
    participant SG as Signal Quality Gate
    participant LOG as Log System
    
    PS->>PS: Test Prerequisites
    PS->>MF: Execute market_filter_module.py
    MF->>LOG: Load portfolio_metrics
    MF->>LOG: Evaluate conditions
    MF->>MF: Save market_filter_status.json
    MF-->>PS: Exit Code 0/1
    
    PS->>SG: Execute signal_quality_gate.py
    SG->>LOG: Load strategy_performance
    SG->>LOG: Load strategy_signals
    SG->>LOG: Evaluate quality
    SG->>SG: Save filtered_signals
    SG->>SG: Save gate_decisions.jsonl
    SG-->>PS: Exit Code 0/1
    
    PS->>PS: Generate Execution Summary
    PS->>LOG: Write bootstrap.log
    PS-->>User: Final Exit Code
```

---

## 5. 의사결정 플로우차트

### [FACT] Market Filter 의사결정 로직
```mermaid
flowchart TD
    A[Load Portfolio Metrics] --> B{realized_pnl < -50?}
    B -->|YES| C[BLOCK - PnL Stop]
    B -->|NO| D{drawdown > 25%?}
    
    D -->|YES| E[BLOCK - Drawdown Stop]
    D -->|NO| F{equity < 9900?}
    
    F -->|YES| G[BLOCK - Equity Stop]
    F -->|NO| H[ALLOW - All OK]
    
    C --> I[Save BLOCK Status]
    E --> I
    G --> I
    H --> J[Save ALLOW Status]
    
    style C fill:#ffebee
    style E fill:#ffebee
    style G fill:#ffebee
    style H fill:#e8f5e8
    style I fill:#ffcdd2
    style J fill:#c8e6c9
```

### [FACT] Signal Quality Gate 의사결정 로직
```mermaid
flowchart TD
    A[Load Strategy Performance] --> B{trades >= 5?}
    B -->|NO| C[ALLOW - Insufficient Data]
    B -->|YES| D{win_rate >= 0.3?}
    
    D -->|NO| E[BLOCK - Low Win Rate]
    D -->|YES| F{pnl >= -5.0?}
    
    F -->|NO| G[BLOCK - Poor PnL]
    F -->|YES| H{hold_time <= 1800s?}
    
    H -->|NO| I[BLOCK - Excessive Hold Time]
    H -->|YES| J[ALLOW - Good Quality]
    
    C --> K[Save to Filtered]
    E --> L[Block Signal]
    G --> L
    I --> L
    J --> K
    
    style C fill:#fff3e0
    style J fill:#e8f5e8
    style K fill:#c8e6c9
    style E fill:#ffebee
    style G fill:#ffebee
    style I fill:#ffebee
    style L fill:#ffcdd2
```

---

## 6. 파일 시스템 플로우차트

### [FACT] 파일 입출력 구조
```mermaid
graph TB
    subgraph "읽기 전용 데이터 소스"
        F1[logs/runtime/portfolio_metrics_snapshot.json]
        F2[logs/runtime/strategy_performance.json]
        F3[logs/runtime/strategy_signals/*.json]
        F4[logs/runtime/runtime_health_summary.json]
    end
    
    subgraph "외부 모듈 처리"
        M1[market_filter_module.py]
        M2[signal_quality_gate.py]
    end
    
    subgraph "출력 결과 파일"
        O1[tools/external_strategy/output/market_filter_status.json]
        O2[tools/external_strategy/output/external_gate_decisions.jsonl]
        O3[tools/external_strategy/output/strategy_signals_filtered/*.json]
    end
    
    subgraph "실행 제어"
        B1[BOOT/start_external_profit_strategy.ps1]
        L1[logs/external_strategy_bootstrap.log]
    end
    
    F1 --> M1
    F4 --> M1
    F2 --> M2
    F3 --> M2
    
    M1 --> O1
    M2 --> O2
    M2 --> O3
    
    B1 --> M1
    B1 --> M2
    B1 --> L1
    
    style F1 fill:#e3f2fd
    style F2 fill:#e3f2fd
    style F3 fill:#e3f2fd
    style F4 fill:#e3f2fd
    style O1 fill:#c8e6c9
    style O2 fill:#c8e6c9
    style O3 fill:#c8e6c9
```

---

## 7. 제약 조건 플로우차트

### [FACT] 헌법 제약 조건 준수 흐름
```mermaid
flowchart TD
    A[외부 전략 설계] --> B{소스 수정 필요?}
    B -->|YES| C[헌법 위반 - 금지]
    B -->|NO| D[헌법 준수 - 허용]
    
    D --> E{외부 모듈만 사용?}
    E -->|YES| F[헌법 준수 - 허용]
    E -->|NO| G[헌법 위반 - 금지]
    
    F --> H{path isolation 유지?}
    H -->|YES| I[헌법 준수 - 허용]
    H -->|NO| J[헌법 위반 - 금지]
    
    I --> K{project root 오염?}
    K -->|NO| L[최종 헌법 준수]
    K -->|YES| M[헌법 위반 - 금지]
    
    style C fill:#ffebee
    style G fill:#ffebee
    style J fill:#ffebee
    style M fill:#ffebee
    style L fill:#c8e6c9
```

---

## 8. 실제 실행 결과 플로우차트

### [FACT] 현재 실행 결과 상태
```mermaid
graph TB
    subgraph "실제 데이터 (2026-03-30 20:30)"
        D1[Equity: 10121.81]
        D2[Realized PnL: -27.10]
        D3[Drawdown: 32.54%]
        D4[Total Signals: 11]
        D5[Allowed: 7]
        D6[Blocked: 4]
    end
    
    subgraph "실행 결과"
        R1[Market Filter: BLOCK]
        R2[Signal Quality: 7/11 허용]
        R3[원본 보존: 11개 무훼손]
        R4[출력 생성: 7개 필터링]
    end
    
    subgraph "최종 상태"
        S1[MVP 구현 완료]
        S2[헌법 준수 완료]
        S3[Gemini 검토 준비]
    end
    
    D1 --> R1
    D2 --> R1
    D3 --> R1
    D4 --> R2
    D5 --> R2
    D6 --> R2
    
    R1 --> S1
    R2 --> S1
    R3 --> S2
    R4 --> S2
    
    S1 --> S3
    S2 --> S3
    
    style R1 fill:#ffcdd2
    style R2 fill:#fff3e0
    style R3 fill:#c8e6c9
    style R4 fill:#c8e6c9
    style S1 fill:#e8f5e8
    style S2 fill:#e8f5e8
    style S3 fill:#e8f5e8
```

---

## 9. 다음 단계 플로우차트

### [FACT] Gemini 검토 이후 흐름
```mermaid
flowchart LR
    A[CANDY MVP 구현 완료] --> B[GEMINI 기술 검토]
    B --> C{기술적 타당성?}
    
    C -->|PASS| D[DENNIS 최종 승인]
    C -->|FAIL| E[수정 요구]
    
    D --> F[운영 배포 준비]
    E --> G[CANDY 수정 재구현]
    G --> B
    
    style A fill:#e8f5e8
    style B fill:#fff3e0
    style D fill:#c8e6c9
    style F fill:#c8e6c9
    style E fill:#ffebee
    style G fill:#fff3e0
```

---

## 10. 최종 요약

### [FACT] 전체 플로우차트 요약
1. **워크플로우**: BAEKSEOL->CANDY->GEMINI->DENNIS (예외 적용)
2. **아키텍처**: 외부 모듈 3계층 (Market Filter, Signal Quality Gate, Bootstrap)
3. **데이터 흐름**: 읽기 전용 → 외부 모듈 → 필터링된 출력
4. **제약 조건**: 소스 수정 금지, 외부 모듈만, path isolation 유지
5. **실행 결과**: Market Filter BLOCK, Signal Quality 7/11 허용
6. **다음 단계**: Gemini 기술 검토 → Dennis 최종 승인

### [FACT] 헌법 준수 상태
- **[FACT]** 소스 수정 금지: 완전 준수
- **[FACT]** 외부 모듈만 사용: 완전 준수  
- **[FACT]** project root 오염 방지: 완전 준수
- **[FACT]** path isolation 유지: 완전 준수
- **[FACT]** FACT 기반 보고: 완전 준수

---

**보고서 완료**: 2026-03-30 20:35  
**작성자**: CANDY (data_validation + execution)  
**헌법**: NEXT-TRADE v1.2.1  
**상태**: COMPLETE FLOWCHART REPORT  
**다음**: GEMINI TECHNICAL REVIEW READY
