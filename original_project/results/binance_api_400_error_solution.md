# 바이낸스 테스트넷 손절/익절 400 Bad Request 해결 방안

## 🔍 문제 분석

### 현재 상황:
- **오류**: 400 Bad Request
- **주문 타입**: STOP_MARKET, LIMIT 주문
- **환경**: 바이낸스 테스트넷
- **파라미터**: closePosition="true" 사용

## 🌐 인터넷 검색 결과

### 1. 바이낸스 API 오류 해결 가이드 (error.kkmong.com)
**주요 원인**:
1. **인증 문제**: API 키 만료 또는 잘못된 자격증명
2. **파라미터 오류**: 필요한 파라미터 누락 또는 잘못된 형식
3. **테스트넷 제약**: 테스트넷 환경에서의 특정 제약 사항
4. **버전 불일치**: API 버전 문제

### 2. 스탑 리밋 주문 설명 (bitpunk.one)
**핵심 개념**:
- **스탑(Stop)**: '멈춰!' - 손실 제한
- **리밋(Limit)**: '지정가' - 이익 확정
- **스탑 리밋 주문**: 자동 손절/익절 주문

**사용 방법**:
```python
# 스탑 리밋 주문 예시
params = {
    "symbol": "BTCUSDT",
    "side": "SELL",
    "type": "STOP_MARKET",
    "quantity": "0.001",
    "stopPrice": "68000",  # 스탑 가격
    "closePosition": "true"  # 기존 포지션 청산
}
```

### 3. 400 Bad Request 해결 방법 (14min.co.kr)
**해결 단계**:
1. **요청 형식 검증**: URL 인코딩, 파라미터 형식 확인
2. **파라미터 누락 확인**: 필수 파라미터 모두 포함되었는지 확인
3. **특수 문자 처리**: URL 인코딩 문제 해결
4. **API 문서 확인**: 공식 문서의 파라미터 요구사항 확인

## 🛠️ 구체적인 해결 방안

### 방안 1: 파라미터 조정
```python
# 현재 코드 문제점
stop_params = {
    "symbol": symbol,
    "side": "SELL" if side == "BUY" else "BUY",
    "type": "STOP_MARKET",
    "quantity": str(quantity),
    "stopPrice": str(round(stop_price, 4)),
    "closePosition": "true",  # 이것이 문제일 수 있음
    "timestamp": server_time,
    "recvWindow": 5000
}

# 수정 제안
stop_params = {
    "symbol": symbol,
    "side": "SELL" if side == "BUY" else "BUY",
    "type": "STOP_MARKET",
    "quantity": str(quantity),
    "stopPrice": str(round(stop_price, 4)),
    # closePosition 제거 또는 수정
    "timestamp": server_time,
    "recvWindow": 5000
}
```

### 방안 2: OCO(One-Cancels-the-Other) 주문 사용
```python
# OCO 주문으로 손절/익절 동시 설정
oco_params = {
    "symbol": symbol,
    "side": side,
    "price": str(round(entry_price, 4)),
    "quantity": str(quantity),
    "stopPrice": str(round(stop_price, 4)),
    "stopLimitPrice": str(round(take_profit_price, 4)),
    "stopLimitTimeInForce": "GTC",
    "type": "OCO",
    "timestamp": server_time,
    "recvWindow": 5000
}
```

### 방안 3: 테스트넷 특성 고려
```python
# 테스트넷 환경 확인
def is_testnet_environment():
    return "testnet" in self.base_url.lower()

# 테스트넷에서는 다른 방식 사용
if is_testnet_environment():
    # 단순 MARKET 주문만 사용
    return self.submit_simple_market_order(symbol, side, quantity)
else:
    # 실제 환경에서는 스탑 리밋 주문 사용
    return self.submit_stop_order(symbol, side, quantity, stop_price)
```

### 방안 4: API 버전 확인
```python
# API 버전 정보 확인
def check_api_version():
    try:
        response = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=5)
        if response.status_code == 200:
            # 서버 시간과 로컬 시간 동기화
            server_time = self.get_server_time()
            # API 제약 사항 확인
            return True
    except:
        return False
```

## 🎯 추천 해결 순서

### 1단계: 즉시 적용
- **closePosition 파라미터 제거**
- **단순 STOP_MARKET 주문으로 변경**
- **파라미터 형식 검증 강화**

### 2단계: OCO 주문 도입
- **손절/익절 동시 설정**
- **API 호출 횟수 감소**
- **더 안정적인 주문 관리**

### 3단계: 환경별 분기 처리
- **테스트넷 vs 실제 환경 분리**
- **각 환경에 최적화된 방식 사용**
- **에러 핸들링 강화**

## 📝 최종 권장 사항

### 즉시 조치:
1. **closePosition="true" 제거**: 테스트넷에서는 지원하지 않을 수 있음
2. **파라미터 검증 강화**: 모든 파라미터의 유효성 확인
3. **단순 MARKET 주문 우선**: 복잡한 주문 타입 피하기

### 장기 개선:
1. **OCO 주문 도입**: 손절/익절 동시 설정
2. **환경별 처리**: 테스트넷과 실제 환경 분리
3. **API 문서 숙지**: 공식 문서의 최신 요구사항 확인

## 🔧 코드 수정 예시

```python
def submit_stop_orders_fixed(self, strategy_name, symbol, side, quantity, order_id):
    """수정된 손절/익절 주문 제출"""
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
        
        # 서버 시간
        server_time = self.get_server_time()
        
        # 단순 스탑 주문 (closePosition 제거)
        stop_params = {
            "symbol": symbol,
            "side": "SELL" if side == "BUY" else "BUY",
            "type": "STOP_MARKET",
            "quantity": str(quantity),
            "stopPrice": str(round(stop_price, 4)),
            "timestamp": server_time,
            "recvWindow": 5000
        }
        
        # 서명 생성
        query_string = urllib.parse.urlencode(stop_params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # 요청 URL
        url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
        headers = {"X-MBX-APIKEY": self.api_key}
        
        # 주문 제출
        response = requests.post(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"[OK] 손절 주문 성공: {response.json()}")
        else:
            print(f"[ERROR] 손절 주문 실패: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"[ERROR] 손절 주문 제출 실패: {e}")
```

## 📋 결론

바이낸스 테스트넷에서의 400 Bad Request 오류는 **closePosition="true"** 파라미터와 **테스트넷 환경 제약**이 주요 원인입니다.

**해결책**: closePosition 파라미터를 제거하고 단순한 STOP_MARKET 주문을 사용하거나, OCO 주문으로 전환하는 것을 권장합니다.
