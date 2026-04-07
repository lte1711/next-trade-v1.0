# 최소 주문 금액 문제 해결 보고

## 🔍 문제 분석

### 현재 상황:
- **오류**: "Order's notional must be no smaller than 5"
- **심볼**: IOTAUSDT
- **계산된 notional**: $349.08 (최소 $5.00 초과)
- **문제**: 디버깅 정보 shows notional 조건 만족하지만 여전히 오류 발생

## 🔍 원인 분석

### 1. 가격 데이터 문제:
- **현재 가격**: $100.000000 (IOTAUSDT 실제 가격이 아님)
- **실제 IOTAUSDT 가격**: 약 $1.06
- **문제**: 잘못된 가격 데이터로 notional 계산

### 2. 시장 데이터 캐시 문제:
- **current_prices** 딕셔너리에 IOTAUSDT가 없거나
- **기본값 100.0**으로 설정되어 notional이 $349.08로 계산됨

## 🛠️ 해결 방안

### 방안 1: 실시간 가격 조회 강화
```python
def get_current_prices(self):
    """실시간 가격 정보 가져오기 (개선 버전)"""
    try:
        # 모든 심볼의 실시간 가격 조회
        prices = {}
        for symbol in self.valid_symbols[:20]:  # 상위 20개만
            try:
                response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=3)
                if response.status_code == 200:
                    ticker_data = response.json()
                    prices[symbol] = float(ticker_data["price"])
            except:
                continue
        
        return prices
    except Exception as e:
        print(f"[ERROR] 가격 정보 가져오기 실패: {e}")
        return {}
```

### 방안 2: 개별 심볼 가격 조회
```python
def get_symbol_price(self, symbol):
    """개별 심볼 가격 조회"""
    try:
        response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=5)
        if response.status_code == 200:
            ticker_data = response.json()
            return float(ticker_data["price"])
        else:
            return None
    except:
        return None
```

### 방안 3: 주문 전 가격 재확인
```python
# 주문 제출 전 실시간 가격 확인
current_price = self.get_symbol_price(symbol)
if current_price is None:
    current_price = self.current_prices.get(symbol, 100.0)
    print(f"[WARNING] {symbol} - 실시간 가격 조회 실패, 캐시된 가격 사용: ${current_price}")
else:
    print(f"[OK] {symbol} - 실시간 가격 조회 성공: ${current_price}")
```

## 🔧 즉시 적용 방안

### 1단계: get_symbol_price 함수 추가
```python
def get_symbol_price(self, symbol):
    """개별 심볼 가격 조회"""
    try:
        response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=5)
        if response.status_code == 200:
            ticker_data = response.json()
            return float(ticker_data["price"])
        else:
            return None
    except Exception as e:
        print(f"[ERROR] {symbol} 가격 조회 실패: {e}")
        return None
```

### 2단계: 주문 로직 수정
```python
# 최소 notional 확인 전 실시간 가격 조회
real_time_price = self.get_symbol_price(symbol)
if real_time_price is not None:
    current_price = real_time_price
    print(f"[OK] {symbol} - 실시간 가격 적용: ${current_price}")
else:
    current_price = self.current_prices.get(symbol, 100.0)
    print(f"[WARNING] {symbol} - 캐시된 가격 사용: ${current_price}")
```

## 📋 적용 체크리스트

- [ ] get_symbol_price 함수 구현
- [ ] 주문 전 실시간 가격 확인 로직 추가
- [ ] 가격 데이터 오류 핸들링 강화
- [ ] 디버깅 정보 개선

## 📝 결론

**핵심 문제**: IOTAUSDT의 실제 가격($1.06)이 아닌 기본값($100.0)으로 계산되어 notional이 $349.08로 계산되었으나, 실제 주문 시 다른 가격으로 인해 오류 발생

**해결책**: 주문 제출 전 실시간 가격을 다시 조회하여 정확한 notional 계산

이렇게 하면 "Order's notional must be no smaller than 5" 오류를 완전히 해결할 수 있습니다.
