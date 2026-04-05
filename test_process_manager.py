#!/usr/bin/env python3
"""ProcessManagerService 문제 진단 테스트"""

import sys
import os
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "merged_partial_v2" / "src"))

def test_module_import():
    """모듈 임포트 테스트"""
    print("🔍 ProcessManagerService 모듈 임포트 테스트 시작...")
    
    try:
        print("  📦 sys.path 설정...")
        print(f"    sys.path[0]: {sys.path[0]}")
        
        print("  📦 merged_partial_v2 패키지 임포트...")
        import merged_partial_v2
        print("  ✅ merged_partial_v2 임포트 성공")
        
        print("  📦 pathing 모듈 임포트...")
        from merged_partial_v2.pathing import install_root as resolve_install_root
        print("  ✅ pathing 임포트 성공")
        
        print("  📦 process_manager_service 모듈 임포트...")
        from merged_partial_v2.services.process_manager_service import _THREAD_LOCK
        print("  ✅ process_manager_service 임포트 성공")
        
        print(f"  🔍 _THREAD_LOCK 타입: {type(_THREAD_LOCK)}")
        print(f"  🔍 _THREAD_LOCK 객체: {_THREAD_LOCK}")
        
        print("  📦 _thread_is_running 함수 임포트...")
        from merged_partial_v2.services.process_manager_service import _thread_is_running
        print("  ✅ _thread_is_running 함수 임포트 성공")
        
        print("  🔄 _thread_is_running 호출 테스트...")
        result = _thread_is_running()
        print(f"  ✅ _thread_is_running() 결과: {result}")
        
        print("  ✅ ProcessManagerService 모듈 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ 모듈 임포트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트"""
    print("🚀 ProcessManagerService 문제 진단 시작\n")
    
    result = test_module_import()
    
    if result:
        print("\n🎉 ProcessManagerService 정상 작동")
    else:
        print("\n❌ ProcessManagerService 문제 발견")
    
    return result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
