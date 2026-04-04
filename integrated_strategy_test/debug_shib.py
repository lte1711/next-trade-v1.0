import requests

try:
    response = requests.get('https://demo-fapi.binance.com/fapi/v1/ticker/24hr?symbol=SHIBUSDT', timeout=10)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'Symbol: {data.get("symbol")}')
        print(f'Price: {data.get("lastPrice")}')
    else:
        print(f'Error: {response.text}')
except Exception as e:
    print(f'Exception: {e}')
