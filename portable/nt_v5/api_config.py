"""
API Configuration - 바이낸스 API 자격증명 관리 모듈
"""

import os
import json


class APIConfig:
    """API 자격증명 설정 관리"""
    
    def __init__(self):
        self.config_file = "api_credentials.json"
        self.load_config()
    
    def load_config(self):
        """설정 파일 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_key = config.get("api_key", "")
                    self.api_secret = config.get("api_secret", "")
                    return
        except Exception:
            pass
        
        # 환경변수 fallback
        self.api_key = self.get_env_var([
            "BINANCE_TESTNET_ACCOUNT_API_KEY",
            "BINANCE_TESTNET_API_KEY", 
            "BINANCE_TESTNET_KEY",
            "BINANCE_API_KEY"
        ])
        
        self.api_secret = self.get_env_var([
            "BINANCE_TESTNET_TRADING_API_SECRET",
            "BINANCE_TESTNET_ACCOUNT_API_SECRET",
            "BINANCE_TESTNET_API_SECRET",
            "BINANCE_TESTNET_SECRET",
            "BINANCE_API_SECRET"
        ])
    
    def get_env_var(self, candidates):
        """환경변수 후보 순서대로 조회"""
        for env_name in candidates:
            value = os.getenv(env_name, "").strip()
            if value:
                return value
        return ""
    
    def save_config(self):
        """설정 파일 저장"""
        try:
            config = {
                "api_key": self.api_key,
                "api_secret": self.api_secret
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def update_credentials(self, api_key, api_secret):
        """자격증명 업데이트"""
        self.api_key = api_key
        self.api_secret = api_secret
        return self.save_config()
    
    def get_credentials(self):
        """자격증명 반환"""
        return self.api_key, self.api_secret
    
    def is_valid(self):
        """자격증명 유효성 검사"""
        return bool(self.api_key and self.api_secret)
    
    def get_base_url(self):
        """기본 URL 반환"""
        return "https://testnet.binancefuture.com"


# 전역 인스턴스
api_config = APIConfig()


def get_api_credentials():
    """API 자격증명 가져오기"""
    return api_config.get_credentials()


def update_api_credentials(api_key, api_secret):
    """API 자격증명 업데이트"""
    return api_config.update_credentials(api_key, api_secret)


def is_api_valid():
    """API 자격증명 유효성 확인"""
    return api_config.is_valid()
