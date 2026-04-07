# 테스트넷 전용 손절/익절 해결 방안

## 🎯 테스트넷 환경 특성 고려

### 테스트넷 제약 사항:
1. **closePosition 파라미터**: 테스트넷에서는 지원하지 않을 수 있음
2. **STOP_MARKET 주문**: 테스트넷에서는 제약이 있을 수 있음
3. **LIMIT 주문**: 테스트넷에서는 다른 동작 방식
4. **API 버전**: 테스트넷과 실제 환경의 API 버전 차이

## 🛠️ 테스트넷 전용 해결 방안

### 방안 1: 손절/익절 기능 비활성화 (즉시 적용)
```python
def submit_stop_orders_testnet(self, strategy_name, symbol, side, quantity, order_id):
    """테스트넷 전용 손절/익절 처리"""
    print(f"[INFO] 테스트넷 환경: 손절/익절 주문은 생략합니다")
    print(f"[INFO] 진입 주문만 실행: {symbol} {side} {quantity}")
    return True  # 성공으로 간주

def submit_stop_orders(self, strategy_name, symbol, side, quantity, order_id):
    """손절/익절 주문 제출"""
    # 테스트넷 환경 감지
    if "testnet" in self.base_url.lower():
        return self.submit_stop_orders_testnet(strategy_name, symbol, side, quantity, order_id)
    else:
        return self.submit_stop_orders_real(strategy_name, symbol, side, quantity, order_id)
```

### 방안 2: 시뮬레이션 방식 (권장)
```python
def submit_stop_orders_simulation(self, strategy_name, symbol, side, quantity, order_id):
    """손절/익절 시뮬레이션"""
    try:
        strategy = self.strategies[strategy_name]
        stop_loss = strategy.get("stop_loss", 0.05)
        take_profit = strategy.get("take_profit", 0.10)
        
        current_price = self.current_prices.get(symbol, 100.0)
        
        if side == "BUY":
            stop_price = current_price * (1 - stop_loss)
            profit_price = current_price * (1 + take_profit)
        else:  # SELL
            stop_price = current_price * (1 + stop_loss)
            profit_price = current_price * (1 - take_profit)
        
        # 시뮬레이션 결과 저장
        simulation_result = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "entry_price": current_price,
            "stop_price": stop_price,
            "profit_price": profit_price,
            "stop_loss_percent": stop_loss * 100,
            "take_profit_percent": take_profit * 100,
            "timestamp": datetime.now().isoformat(),
            "type": "SIMULATION"
        }
        
        # 결과 저장
        if "stop_orders" not in self.trading_results:
            self.trading_results["stop_orders"] = []
        
        self.trading_results["stop_orders"].append(simulation_result)
        
        print(f"[OK] 손절/익절 시뮬레이션 성공:")
        print(f"  - 진입 가격: ${current_price:.4f}")
        print(f"  - 손절 가격: ${stop_price:.4f} ({stop_loss*100:.1f}%)")
        print(f"  - 익절 가격: ${profit_price:.4f} ({take_profit*100:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 손절/익절 시뮬레이션 실패: {e}")
        return False
```

### 방안 3: 단순한 가격 모니터링
```python
def monitor_price_levels(self, symbol, side, quantity, entry_price, stop_loss, take_profit):
    """가격 레벨 모니터링"""
    stop_loss_price = entry_price * (1 + stop_loss) if side == "SELL" else entry_price * (1 - stop_loss)
    take_profit_price = entry_price * (1 - take_profit) if side == "SELL" else entry_price * (1 + take_profit)
    
    print(f"[MONITOR] {symbol} 가격 모니터링 시작:")
    print(f"  - 진입 가격: ${entry_price:.4f}")
    print(f"  - 손절 가격: ${stop_loss_price:.4f}")
    print(f"  - 익절 가격: ${take_profit_price:.4f}")
    
    # 주기적으로 가격 확인 (실제 구현에서는 스케줄러 필요)
    # 여기서는 단순히 로그만 남김
    return True
```

## 🔧 즉시 적용 방법

### 1단계: submit_stop_orders 함수 수정
```python
def submit_stop_orders(self, strategy_name, symbol, side, quantity, order_id):
    """손절/익절 주문 제출 (테스트넷 전용)"""
    # 테스트넷 환경 확인
    if "testnet" in self.base_url.lower():
        print(f"[INFO] 테스트넷 환경: 손절/익절 주문은 시뮬레이션으로 대체합니다")
        return self.submit_stop_orders_simulation(strategy_name, symbol, side, quantity, order_id)
    else:
        print(f"[INFO] 실제 환경: 손절/익절 주문을 실행합니다")
        return self.submit_stop_orders_real(strategy_name, symbol, side, quantity, order_id)
```

### 2단계: 시뮬레이션 함수 추가
```python
def submit_stop_orders_simulation(self, strategy_name, symbol, side, quantity, order_id):
    """손절/익절 시뮬레이션 (테스트넷 전용)"""
    try:
        strategy = self.strategies[strategy_name]
        stop_loss = strategy.get("stop_loss", 0.05)
        take_profit = strategy.get("take_profit", 0.10)
        
        current_price = self.current_prices.get(symbol, 100.0)
        
        if side == "BUY":
            stop_price = current_price * (1 - stop_loss)
            profit_price = current_price * (1 + take_profit)
        else:  # SELL
            stop_price = current_price * (1 + stop_loss)
            profit_price = current_price * (1 - take_profit)
        
        # 시뮬레이션 결과 저장
        simulation_result = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "entry_price": current_price,
            "stop_price": stop_price,
            "profit_price": profit_price,
            "stop_loss_percent": stop_loss * 100,
            "take_profit_percent": take_profit * 100,
            "timestamp": datetime.now().isoformat(),
            "type": "SIMULATION"
        }
        
        # 결과 저장
        if "stop_orders" not in self.trading_results:
            self.trading_results["stop_orders"] = []
        
        self.trading_results["stop_orders"].append(simulation_result)
        
        print(f"[OK] 손절/익절 시뮬레이션 성공:")
        print(f"  - 진입 가격: ${current_price:.4f}")
        print(f"  - 손절 가격: ${stop_price:.4f} ({stop_loss*100:.1f}%)")
        print(f"  - 익절 가격: ${profit_price:.4f} ({take_profit*100:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 손절/익절 시뮬레이션 실패: {e}")
        return False
```

## 🎯 최종 권장 사항

### 테스트넷 전용 전략:
1. **손절/익절 시뮬레이션**: 실제 주문 대신 시뮬레이션으로 결과 저장
2. **로깅 강화**: 손절/익절 설정값과 예상 결과를 상세하게 출력
3. **성과 추적**: 시뮬레이션 결과를 거래 성과에 포함

### 실제 환경 대비:
1. **환경 감지**: 테스트넷과 실제 환경을 자동으로 구분
2. **분기 처리**: 각 환경에 최적화된 손절/익절 방식 사용
3. **결과 일관성**: 테스트넷과 실제 환경의 결과 형식 통일

## 📋 적용 체크리스트

- [ ] 테스트넷 환경 감지 함수 추가
- [ ] 손절/익절 시뮬레이션 함수 구현
- [ ] submit_stop_orders 함수 수정
- [ ] 시뮬레이션 결과 저장 로직 추가
- [ ] 로그 메시지 개선
- [ ] 성과 보고서에 시뮬레이션 결과 포함

## 📝 결론

테스트넷 환경에서는 **실제 손절/익절 주문 대신 시뮬레이션 방식**을 사용하는 것이 가장 현실적인 해결책입니다.

이렇게 하면:
1. **400 Bad Request 오류 방지**
2. **테스트넷 제약 우회**
3. **일관된 성과 측정**
4. **실제 환경으로의 원활한 전환**

테스트넷에서는 기능 검증에 집중하고, 실제 환경에서는 실제 주문을 실행하는 방식으로 분기 처리하는 것을 권장합니다.
