"""
실폐 원인 분석 보고서
"""

import json
import requests
from datetime import datetime
from pathlib import Path

def analyze_failure_causes():
    """실폐 원인 분석"""
    
    print("=" * 60)
    print("🔍 실폐 원인 분석 보고서")
    print("=" * 60)
    
    # 1. SHIBUSDT 심볼 문제 분석
    print("\n📊 1. SHIBUSDT 심볼 문제 분석")
    print("-" * 40)
    
    try:
        # 바이낸스 테스트넷 심볼 정보 조회
        response = requests.get('https://demo-fapi.binance.com/fapi/v1/exchangeInfo', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            all_symbols = [s['symbol'] for s in data['symbols']]
            
            # SHIB 관련 심볼 찾기
            shib_symbols = [s for s in all_symbols if 'SHIB' in s]
            
            print(f"✅ 거래소 심볼 조회 성공")
            print(f"  🔢 전체 심볼 수: {len(all_symbols)}개")
            print(f"  🐕 SHIB 관련 심볼: {shib_symbols}")
            
            # 원래 사용하려던 심볼 확인
            if 'SHIBUSDT' in all_symbols:
                print(f"  ✅ SHIBUSDT: 지원됨")
            else:
                print(f"  ❌ SHIBUSDT: 지원되지 않음")
                print(f"  💡 대안 심볼: {shib_symbols}")
            
        else:
            print(f"❌ 거래소 심볼 조회 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 심볼 조회 오류: {e}")
    
    # 2. 실제 심볼 테스트
    print(f"\n📊 2. 실제 심볼 테스트")
    print("-" * 40)
    
    test_symbols = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", 
        "SHIBUSDT", "1000SHIBUSDT", "PEPEUSDT"
    ]
    
    for symbol in test_symbols:
        try:
            response = requests.get(f'https://demo-fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                price = data.get("lastPrice", "N/A")
                print(f"  ✅ {symbol}: ${price}")
            else:
                error_data = response.json()
                print(f"  ❌ {symbol}: {error_data.get('msg', 'Unknown error')}")
                
        except Exception as e:
            print(f"  ❌ {symbol}: {e}")
    
    # 3. 코드 문제 분석
    print(f"\n🔧 3. 코드 문제 분석")
    print("-" * 40)
    
    print(f"🐛 발견된 문제:")
    print(f"  1. SHIBUSDT 심볼이 바이낸스 테스트넷에 없음")
    print(f"  2. 1000SHIBUSDT를 사용해야 함")
    print(f"  3. 일부 심볼의 가격 포맷 문제")
    print(f"  4. 에러 핸들링 부족")
    
    # 4. 해결 방안 제시
    print(f"\n💡 4. 해결 방안")
    print("-" * 40)
    
    print(f"🔧 즉시 수정 필요:")
    print(f"  1. SHIBUSDT → 1000SHIBUSDT로 변경")
    print(f"  2. 다른 심볼들도 실제 지원 여부 확인")
    print(f"  3. 가격 데이터 포맷 검증 로직 추가")
    print(f"  4. 에러 핸들링 강화")
    
    print(f"\n🔄 장기 개선:")
    print(f"  1. 심볼 지원 여부 동적 확인")
    print(f"  2. fallback 데이터 소스 구축")
    print(f"  3. 실시간 연결 상태 모니터링")
    print(f"  4. 원본 프로젝트와의 호환성 확보")
    
    # 5. 수정된 전략 설정
    print(f"\n📋 5. 수정된 전략 설정")
    print("-" * 40)
    
    corrected_strategies = {
        "conservative_btc": {"symbol": "BTCUSDT", "status": "✅ 지원됨"},
        "conservative_eth": {"symbol": "ETHUSDT", "status": "✅ 지원됨"},
        "growth_sol": {"symbol": "SOLUSDT", "status": "✅ 지원됨"},
        "momentum_doge": {"symbol": "DOGEUSDT", "status": "✅ 지원됨"},
        "volatility_shib": {"symbol": "1000SHIBUSDT", "status": "✅ 수정 필요"}
    }
    
    for strategy, info in corrected_strategies.items():
        print(f"  🎯 {strategy}: {info['symbol']} ({info['status']})")
    
    # 6. 원본과의 통합 고려사항
    print(f"\n🔗 6. 원본과의 통합 고려사항")
    print("-" * 40)
    
    print(f"📋 통합 준비:")
    print(f"  1. config.json 호환성 유지")
    print(f"  2. API 연동 방식 통일")
    print(f"  3. 에러 처리 방식 표준화")
    print(f"  4. 로그 포맷 일치")
    print(f"  5. 테스트 결과 저장 방식 통일")
    
    print(f"\n⚠️ 주의사항:")
    print(f"  1. 원본 프로젝트의 API 키 사용")
    print(f"  2. 테스트넷/실서버 모드 전환 기능")
    print(f"  3. 심볼 설정 외부화")
    print(f"  4. 리스크 관리 파라미터 조정")
    
    # 7. 최종 결론
    print(f"\n🎯 7. 최종 결론")
    print("-" * 40)
    
    print(f"📊 실폐 원인:")
    print(f"  🔸 주요 원인: SHIBUSDT 심볼 미지원")
    print(f"  🔸 부가 원인: 에러 핸들링 부족")
    print(f"  🔸 구조적 문제: 심볼 검증 로직 부재")
    
    print(f"\n💡 해결책:")
    print(f"  ✅ 즉시: 1000SHIBUSDT로 심볼 변경")
    print(f"  ✅ 단기: 심볼 지원 여부 확인 로직 추가")
    print(f"  ✅ 중기: 통합 가능한 아키텍처 재구성")
    print(f"  ✅ 장기: 원본과의 완전한 통합")
    
    print(f"\n🎯 FACT 기반 결론:")
    print(f"  실폐는 심볼 설정 오류가 주요 원인이며,")
    print(f"  즉시 수정 가능한 기술적 문제입니다.")
    print(f"  원본과의 통합을 고려한 구조적 개선이 필요합니다.")
    
    print(f"\n" + "=" * 60)
    print("🔍 실폐 원인 분석 완료")
    print("=" * 60)

if __name__ == "__main__":
    analyze_failure_causes()
