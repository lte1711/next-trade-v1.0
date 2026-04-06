#!/usr/bin/env python3
"""
테스트 데이터 로드 스크립트 - JSON 구조 확인
"""

import json
import pandas as pd

def test_data_loading():
    """데이터 로드 테스트"""
    data_path = "data/backtest_cache_v2/BTCUSDT_5m_5.0y.json"
    
    print("📊 데이터 로드 테스트")
    print("=" * 40)
    
    # JSON 데이터 로드
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    print(f"📋 데이터 타입: {type(data)}")
    print(f"📋 데이터 길이: {len(data)}")
    
    if len(data) > 0:
        print(f"📋 첫 번째 요소 타입: {type(data[0])}")
        print(f"📋 첫 번째 요소 길이: {len(data[0])}")
        print(f"📋 첫 번째 요소: {data[0]}")
    
    # DataFrame으로 변환 시도
    try:
        df = pd.DataFrame(data)
        print(f"✅ DataFrame 변환 성공: {df.shape}")
        print(f"📋 컬럼: {list(df.columns)}")
        
        # 첫 5개 행 출력
        print("📋 첫 5개 행:")
        print(df.head())
        
    except Exception as e:
        print(f"❌ DataFrame 변환 실패: {e}")
        
        # 수동으로 변환
        if len(data) > 0:
            sample = data[0]
            print(f"📋 샘플 데이터: {sample}")
            
            # 필요한 컬럼만 추출
            if len(sample) >= 5:
                filtered_data = []
                for item in data:
                    if len(item) >= 5:
                        filtered_data.append([item[0], item[1], item[2], item[3], item[4]])
                
                df_filtered = pd.DataFrame(filtered_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                print(f"✅ 필터링된 DataFrame: {df_filtered.shape}")
                print("📋 필터링된 첫 5개 행:")
                print(df_filtered.head())

if __name__ == "__main__":
    test_data_loading()
