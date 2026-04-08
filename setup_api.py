"""
API Setup - 바이낸스 API 자격증명 설정 스크립트
"""

from api_config import update_api_credentials


def main():
    """API 자격증명 설정"""
    print("=== 바이낸스 API 자격증명 설정 ===")
    print()
    
    print("1. 테스트넷 API 자격증명을 입력해주세요.")
    print("2. 실제 거래 시에는 반드시 실제 계정의 API를 사용해주세요.")
    print()
    
    api_key = input("API Key: ").strip()
    api_secret = input("API Secret: ").strip()
    
    if not api_key or not api_secret:
        print("[ERROR] API Key와 API Secret을 모두 입력해주세요.")
        return
    
    if update_api_credentials(api_key, api_secret):
        print("[SUCCESS] API 자격증명이 성공적으로 저장되었습니다.")
        print(f"저장 위치: api_credentials.json")
        print()
        print("이제 main_runtime.py를 실행할 수 있습니다.")
    else:
        print("[ERROR] API 자격증명 저장에 실패했습니다.")


if __name__ == "__main__":
    main()
