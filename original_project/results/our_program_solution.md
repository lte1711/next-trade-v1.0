# 우리 프로그램에 맞는 손절/익절 해결 방안

## 🔍 현재 코드 분석

### 문제점 파악:
```python
# 현재 손절 주문 (548-549라인)
stop_params = {
    "symbol": symbol,
    "side": "SELL" if side == "BUY" else "BUY",
    "type": "STOP_MARKET",
    "quantity": str(quantity),
    "stopPrice": str(round(stop_price, 4)),
    "closePosition": "true",  # 이것이 문제!
    "timestamp": server_time,
    "recvWindow": 5000
}

# 현재 익절 주문 (577-578라인)
profit_params = {
    "symbol": symbol,
    "side": "SELL" if side == "BUY" else "BUY",
    "type": "LIMIT",
    "quantity": str(quantity),
    "price": str(round(profit_price, 4)),
    "closePosition": "true",  # 이것도 문제!
    "timeInForce": "GTC",
    "timestamp": server_time,
    "recvWindow": 5000
}
```

## 🛠️ 우리 프로그램에 맞는 해결 방안

### 방안 1: closePosition 파라미터 제거 (즉시 적용)
```python
def submit_stop_orders_fixed(self, strategy_name, symbol, side, quantity, order_id):
    """손절/익절 주문 제출 (수정 버전)"""
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
        
        server_time = self.get_server_time()
        
        # 손절 주문 (closePosition 제거)
        stop_params = {
            "symbol": symbol,
            "side": "SELL" if side == "BUY" else "BUY",
            "type": "STOP_MARKET",
            "quantity": str(quantity),
            "stopPrice": str(round(stop_price, 4)),
            "timestamp": server_time,
            "recvWindow": 5000
        }
        
        # 서명 및 요청
        stop_query = urllib.parse.urlencode(stop_params)
        stop_signature = hmac.new(
            self.api_secret.encode("utf-8"),
            stop_query.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        stop_url = f"{self.base_url}/fapi/v1/order?{stop_query}&signature={stop_signature}"
        stop_headers = {"X-MBX-APIKEY": self.api_key}
        
        stop_response = requests.post(stop_url, headers=stop_headers, timeout=10)
        
        if stop_response.status_code == 200:
            print(f"[OK] 손절 주문 성공: {stop_response.json()}")
        else:
            print(f"[ERROR] 손절 주문 실패: {stop_response.status_code} - {stop_response.text}")
        
        # 익절 주문 (closePosition 제거)
        profit_params = {
            "symbol": symbol,
            "side": "SELL" if side == "BUY" else "BUY",
            "type": "LIMIT",
            "quantity": str(quantity),
            "price": str(round(profit_price, 4)),
            "timeInForce": "GTC",
            "timestamp": server_time,
            "recvWindow": 5000
        }
        
        profit_query = urllib.parse.urlencode(profit_params)
        profit_signature = hmac.new(
            self.api_secret.encode("utf-8"),
            profit_query.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        profit_url = f"{self.base_url}/fapi/v1/order?{profit_query}&signature={profit_signature}"
        profit_headers = {"X-MBX-APIKEY": self.api_key}
        
        profit_response = requests.post(profit_url, headers=profit_headers, timeout=10)
        
        if profit_response.status_code == 200:
            print(f"[OK] 익절 주문 성공: {profit_response.json()}")
        else:
            print(f"[ERROR] 익절 주문 실패: {profit_response.status_code} - {profit_response.text}")
                
    except Exception as e:
        print(f"[ERROR] 손절/익절 주문 실패: {e}")
```

### 방안 2: OCO 주문으로 통합 (권장)
```python
def submit_stop_orders_oco(self, strategy_name, symbol, side, quantity, order_id):
    """OCO 주문으로 손절/익절 동시 설정"""
    try:
        strategy = self.strategies[strategy_name]
        stop_loss = strategy.get("stop_loss", 0.05)
        take_profit = strategy.get("take_profit", 0.10)
        
        current_price = self.current_prices.get(symbol, 100.0)
        
        if side == "BUY":
            stop_price = current_price * (1 - stop_loss)
            profit_price = current_price * (1 + take_profit)
            entry_price = current_price  # 시장가 진입
        else:  # SELL
            stop_price = current_price * (1 + stop_loss)
            profit_price = current_price * (1 - take_profit)
            entry_price = current_price  # 시장가 진입
        
        server_time = self.get_server_time()
        
        # OCO 주문 파라미터
        oco_params = {
            "symbol": symbol,
            "side": side,
            "quantity": str(quantity),
            "price": str(round(entry_price, 4)),  # 진입 가격
            "stopPrice": str(round(stop_price, 4)),  # 손절 가격
            "stopLimitPrice": str(round(profit_price, 4)),  # 익절 가격
            "stopLimitTimeInForce": "GTC",
            "type": "OCO",
            "timestamp": server_time,
            "recvWindow": 5000
        }
        
        # 서명 및 요청
        oco_query = urllib.parse.urlencode(oco_params)
        oco_signature = hmac.new(
            self.api_secret.encode("utf-8"),
            oco_query.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        oco_url = f"{self.base_url}/fapi/v1/order/oco?{oco_query}&signature={oco_signature}"
        oco_headers = {"X-MBX-APIKEY": self.api_key}
        
        oco_response = requests.post(oco_url, headers=oco_headers, timeout=10)
        
        if oco_response.status_code == 200:
            result = oco_response.json()
            print(f"[OK] OCO 주문 성공: {result}")
            return result
        else:
            print(f"[ERROR] OCO 주문 실패: {oco_response.status_code} - {oco_response.text}")
            return None
                
    except Exception as e:
        print(f"[ERROR] OCO 주문 실패: {e}")
        return None
```

### 방안 3: 테스트넷 환경 감지
```python
def is_testnet_environment(self):
    """테스트넷 환경인지 확인"""
    return "testnet" in self.base_url.lower()

def submit_stop_orders_adaptive(self, strategy_name, symbol, side, quantity, order_id):
    """환경에 따른 적응형 손절/익절 주문"""
    if self.is_testnet_environment():
        # 테스트넷에서는 단순 주문만 사용
        print("[INFO] 테스트넷 환경: 손절/익절 주문 건너뜀")
        return None
    else:
        # 실제 환경에서는 OCO 주문 사용
        return self.submit_stop_orders_oco(strategy_name, symbol, side, quantity, order_id)
```

## 🔧 즉시 적용 방법

### 1단계: submit_stop_orders 함수 수정
```python
# 522-599라인을 완전히 교체
def submit_stop_orders(self, strategy_name, symbol, side, quantity, order_id):
    """손절/익절 주문 제출 (수정 버전)"""
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
        
        server_time = self.get_server_time()
        
        # 손절 주문 (closePosition 제거)
        stop_params = {
            "symbol": symbol,
            "side": "SELL" if side == "BUY" else "BUY",
            "type": "STOP_MARKET",
            "quantity": str(quantity),
            "stopPrice": str(round(stop_price, 4)),
            "timestamp": server_time,
            "recvWindow": 5000
        }
        
        # 서명 및 요청
        stop_query = urllib.parse.urlencode(stop_params)
        stop_signature = hmac.new(
            self.api_secret.encode("utf-8"),
            stop_query.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        stop_url = f"{self.base_url}/fapi/v1/order?{stop_query}&signature={stop_signature}"
        stop_headers = {"X-MBX-APIKEY": self.api_key}
        
        stop_response = requests.post(stop_url, headers=stop_headers, timeout=10)
        
        if stop_response.status_code == 200:
            print(f"[OK] 손절 주문 성공: {stop_response.json()}")
        else:
            print(f"[ERROR] 손절 주문 실패: {stop_response.status_code} - {stop_response.text}")
        
        # 익절 주문 (closePosition 제거)
        profit_params = {
            "symbol": symbol,
            "side": "SELL" if side == "BUY" else "BUY",
            "type": "LIMIT",
            "quantity": str(quantity),
            "price": str(round(profit_price, 4)),
            "timeInForce": "GTC",
            "timestamp": server_time,
            "recvWindow": 5000
        }
        
        profit_query = urllib.parse.urlencode(profit_params)
        profit_signature = hmac.new(
            self.api_secret.encode("utf-8"),
            profit_query.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        profit_url = f"{self.base_url}/fapi/v1/order?{profit_query}&signature={profit_signature}"
        profit_headers = {"X-MBX-APIKEY": self.api_key}
        
        profit_response = requests.post(profit_url, headers=profit_headers, timeout=10)
        
        if profit_response.status_code == 200:
            print(f"[OK] 익절 주문 성공: {profit_response.json()}")
        else:
            print(f"[ERROR] 익절 주문 실패: {profit_response.status_code} - {profit_response.text}")
                
    except Exception as e:
        print(f"[ERROR] 손절/익절 주문 실패: {e}")
```

### 2단계: submit_order 함수 호출 수정
```python
# 509-510라인 수정
# 기존
# self.submit_stop_orders(strategy_name, symbol, side, quantity, result.get("orderId"))

# 수정 (에러 핸들링 추가)
try:
    self.submit_stop_orders(strategy_name, symbol, side, quantity, result.get("orderId"))
except Exception as e:
    print(f"[WARNING] 손절/익절 주문 실패: {e}")
    print("[INFO] 진입 주문은 성공했으나 손절/익절은 설정되지 않음")
```

## 🎯 최종 권장 사항

### 즉시 적용:
1. **closePosition 파라미터 제거**: 548라인과 577라인에서 `"closePosition": "true"` 제거
2. **에러 핸들링 강화**: 손절/익절 실패 시에도 진입 주문은 유지
3. **로그 개선**: 실패 원인을 더 상세하게 출력

### 장기 개선:
1. **OCO 주문 도입**: 하나의 주문으로 손절/익절 동시 설정
2. **환경 감지**: 테스트넷과 실제 환경 분리 처리
3. **API 버전 확인**: 바이낸스 API 최신 문서에 맞춰 업데이트

## 📋 적용 체크리스트

- [ ] closePosition 파라미터 제거
- [ ] 에러 핸들링 강화
- [ ] OCO 주문 구현
- [ ] 테스트넷 환경 감지
- [ ] API 문서 최신화

이 방안들을 적용하면 바이낸스 테스트넷에서의 400 Bad Request 오류를 해결할 수 있습니다.
