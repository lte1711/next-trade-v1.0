"""
원본 프로젝트와의 호환성 확인 모듈
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

class CompatibilityChecker:
    """원본 프로젝트 호환성 확인기"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.original_root = self.project_root.parent
        self.original_config = self.original_root / "config.json"
        self.original_app = self.original_root / "src" / "next_trade" / "api" / "app.py"
        self.original_investor_service = self.original_root / "src" / "next_trade" / "api" / "investor_service.py"
        
        self.compatibility_results = {}
    
    def check_all_compatibility(self) -> Dict[str, Any]:
        """전체 호환성 확인"""
        
        print("FACT: 원본 프로젝트 호환성 확인 시작")
        
        results = {
            "config_compatibility": self.check_config_compatibility(),
            "api_compatibility": self.check_api_compatibility(),
            "data_structure_compatibility": self.check_data_structure_compatibility(),
            "dependency_compatibility": self.check_dependency_compatibility(),
            "integration_readiness": self.check_integration_readiness()
        }
        
        self.compatibility_results = results
        
        # 전체 호환성 평가
        overall_compatibility = self._evaluate_overall_compatibility(results)
        results["overall_compatibility"] = overall_compatibility
        
        print(f"FACT: 호환성 확인 완료")
        print(f"  - 전체 호환성: {overall_compatibility['status']}")
        print(f"  - 호환성 점수: {overall_compatibility['score']}/100")
        
        return results
    
    def check_config_compatibility(self) -> Dict[str, Any]:
        """설정 호환성 확인"""
        
        result = {
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        # 원본 설정 파일 확인
        if not self.original_config.exists():
            result["status"] = "error"
            result["issues"].append("원본 config.json 파일이 없습니다")
            return result
        
        try:
            with open(self.original_config, 'r', encoding='utf-8') as f:
                original_config = json.load(f)
            
            # 바이낸스 설정 확인
            if "binance_testnet" in original_config:
                result["details"]["binance_config"] = "✅ 있음"
                binance_config = original_config["binance_testnet"]
                
                # 필수 키 확인
                required_keys = ["api_key", "api_secret", "base_url"]
                missing_keys = [key for key in required_keys if key not in binance_config]
                
                if missing_keys:
                    result["issues"].append(f"바이낸스 설정에 필수 키가 없습니다: {missing_keys}")
                    result["details"]["binance_keys"] = "❌ 부족"
                else:
                    result["details"]["binance_keys"] = "✅ 완전"
                
                result["status"] = "compatible"
            else:
                result["details"]["binance_config"] = "❌ 없음"
                result["issues"].append("바이낸스 설정이 없습니다")
                result["status"] = "partial"
            
            # 기타 설정 확인
            other_settings = ["testnet_initial_equity", "binance_execution_mode", "binance_probe_mode"]
            for setting in other_settings:
                if setting in original_config:
                    result["details"][setting] = "✅ 있음"
                else:
                    result["details"][setting] = "⚠️ 없음"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"설정 파일 읽기 오류: {e}")
        
        return result
    
    def check_api_compatibility(self) -> Dict[str, Any]:
        """API 호환성 확인"""
        
        result = {
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        # 원본 API 파일 확인
        if not self.original_app.exists():
            result["status"] = "error"
            result["issues"].append("원본 app.py 파일이 없습니다")
            return result
        
        if not self.original_investor_service.exists():
            result["status"] = "error"
            result["issues"].append("원본 investor_service.py 파일이 없습니다")
            return result
        
        try:
            # app.py 구조 확인
            with open(self.original_app, 'r', encoding='utf-8') as f:
                app_content = f.read()
            
            # 필수 임포트 확인
            required_imports = ["FastAPI", "routes_v1_investor", "routes_v1_ops"]
            for import_name in required_imports:
                if import_name in app_content:
                    result["details"][f"import_{import_name}"] = "✅ 있음"
                else:
                    result["details"][f"import_{import_name}"] = "❌ 없음"
                    result["issues"].append(f"필수 임포트가 없습니다: {import_name}")
            
            # investor_service.py 구조 확인
            with open(self.original_investor_service, 'r', encoding='utf-8') as f:
                service_content = f.read()
            
            # 필수 함수 확인
            required_functions = ["_project_root", "_load_config_from_json"]
            for func_name in required_functions:
                if func_name in service_content:
                    result["details"][f"function_{func_name}"] = "✅ 있음"
                else:
                    result["details"][f"function_{func_name}"] = "❌ 없음"
                    result["issues"].append(f"필수 함수가 없습니다: {func_name}")
            
            if not result["issues"]:
                result["status"] = "compatible"
            else:
                result["status"] = "partial"
            
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"API 파일 읽기 오류: {e}")
        
        return result
    
    def check_data_structure_compatibility(self) -> Dict[str, Any]:
        """데이터 구조 호환성 확인"""
        
        result = {
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        # 원본 데이터 구조 확인
        original_data_files = [
            "fixed_strategy_1year_report.json",
            "maximized_return_1year_report.json",
            "enhanced_strategy_with_additional_report.json",
            "extreme_100percent_target_report.json"
        ]
        
        for file_name in original_data_files:
            file_path = self.original_root / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 필수 구조 확인
                    required_keys = ["report_metadata", "simulation_summary", "total_performance"]
                    missing_keys = [key for key in required_keys if key not in data]
                    
                    if missing_keys:
                        result["details"][file_name] = "❌ 구조 불일치"
                        result["issues"].append(f"{file_name}에 필수 키가 없습니다: {missing_keys}")
                    else:
                        result["details"][file_name] = "✅ 호환"
                
                except Exception as e:
                    result["details"][file_name] = "❌ 읽기 오류"
                    result["issues"].append(f"{file_name} 읽기 오류: {e}")
            else:
                result["details"][file_name] = "⚠️ 파일 없음"
        
        if not result["issues"]:
            result["status"] = "compatible"
        elif len(result["issues"]) < len(original_data_files) / 2:
            result["status"] = "partial"
        else:
            result["status"] = "incompatible"
        
        return result
    
    def check_dependency_compatibility(self) -> Dict[str, Any]:
        """의존성 호환성 확인"""
        
        result = {
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        # 원본 requirements.txt 확인
        original_requirements = self.original_root / "requirements.txt"
        integrated_requirements = self.project_root / "requirements.txt"
        
        if original_requirements.exists():
            try:
                with open(original_requirements, 'r', encoding='utf-8') as f:
                    original_deps = f.read().splitlines()
                
                result["details"]["original_requirements"] = f"✅ {len(original_deps)}개 패키지"
                
                # 중요 패키지 확인
                important_packages = ["fastapi", "uvicorn", "requests", "python-dotenv"]
                for package in important_packages:
                    if any(package in dep for dep in original_deps):
                        result["details"][f"package_{package}"] = "✅ 있음"
                    else:
                        result["details"][f"package_{package}"] = "⚠️ 없음"
                
            except Exception as e:
                result["issues"].append(f"원본 requirements.txt 읽기 오류: {e}")
        
        if integrated_requirements.exists():
            try:
                with open(integrated_requirements, 'r', encoding='utf-8') as f:
                    integrated_deps = f.read().splitlines()
                
                result["details"]["integrated_requirements"] = f"✅ {len(integrated_deps)}개 패키지"
                
                # 중복 확인
                original_set = set(original_deps) if original_requirements.exists() else set()
                integrated_set = set(integrated_deps)
                
                conflicts = original_set.intersection(integrated_set)
                result["details"]["conflicting_packages"] = f"⚠️ {len(conflicts)}개 중복"
                
            except Exception as e:
                result["issues"].append(f"통합 requirements.txt 읽기 오류: {e}")
        
        if not result["issues"]:
            result["status"] = "compatible"
        else:
            result["status"] = "partial"
        
        return result
    
    def check_integration_readiness(self) -> Dict[str, Any]:
        """통합 준비 상태 확인"""
        
        result = {
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        # 통합 모듈 확인
        integration_modules = [
            "integration/compatibility.py",
            "integration/merger.py"
        ]
        
        for module_path in integration_modules:
            full_path = self.project_root / module_path
            if full_path.exists():
                result["details"][module_path] = "✅ 준비 완료"
            else:
                result["details"][module_path] = "⚠️ 준비 필요"
                result["issues"].append(f"통합 모듈이 없습니다: {module_path}")
        
        # 설정 호환성 확인
        config_compatible = self.check_config_compatibility()
        if config_compatible["status"] == "compatible":
            result["details"]["config_integration"] = "✅ 준비 완료"
        else:
            result["details"]["config_integration"] = "⚠️ 준비 필요"
            result["issues"].append("설정 통합 준비 필요")
        
        # API 연동 확인
        api_compatible = self.check_api_compatibility()
        if api_compatible["status"] in ["compatible", "partial"]:
            result["details"]["api_integration"] = "✅ 준비 완료"
        else:
            result["details"]["api_integration"] = "⚠️ 준비 필요"
            result["issues"].append("API 통합 준비 필요")
        
        if not result["issues"]:
            result["status"] = "ready"
        elif len(result["issues"]) < 3:
            result["status"] = "partial"
        else:
            result["status"] = "not_ready"
        
        return result
    
    def _evaluate_overall_compatibility(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """전체 호환성 평가"""
        
        status_scores = {
            "compatible": 100,
            "partial": 60,
            "ready": 90,
            "not_ready": 20,
            "unknown": 0,
            "error": 0,
            "incompatible": 10
        }
        
        scores = []
        for check_name, check_result in results.items():
            if check_name == "overall_compatibility":
                continue
            
            status = check_result.get("status", "unknown")
            scores.append(status_scores.get(status, 0))
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 전체 상태 결정
        if avg_score >= 80:
            overall_status = "compatible"
        elif avg_score >= 60:
            overall_status = "partial"
        elif avg_score >= 40:
            overall_status = "needs_work"
        else:
            overall_status = "incompatible"
        
        return {
            "status": overall_status,
            "score": round(avg_score, 1),
            "individual_scores": {
                check_name: status_scores.get(check_result.get("status", "unknown"), 0)
                for check_name, check_result in results.items()
                if check_name != "overall_compatibility"
            }
        }
    
    def get_integration_plan(self) -> Dict[str, Any]:
        """통합 계획 생성"""
        
        if not self.compatibility_results:
            self.check_all_compatibility()
        
        plan = {
            "priority_tasks": [],
            "optional_tasks": [],
            "blocking_issues": [],
            "estimated_effort": "medium"
        }
        
        # 우선 과업
        config_result = self.compatibility_results.get("config_compatibility", {})
        if config_result.get("status") != "compatible":
            plan["priority_tasks"].append("설정 파일 호환성 확보")
        
        api_result = self.compatibility_results.get("api_compatibility", {})
        if api_result.get("status") != "compatible":
            plan["priority_tasks"].append("API 연동 경로 확보")
        
        # 차단 이슈
        for check_name, check_result in self.compatibility_results.items():
            if check_result.get("status") == "error":
                plan["blocking_issues"].append(f"{check_name} 심각한 문제")
        
        # 선택 과업
        plan["optional_tasks"].extend([
            "데이터 구조 최적화",
            "의존성 정리",
            "테스트 커버리지 확대"
        ])
        
        return plan
    
    def generate_compatibility_report(self) -> str:
        """호환성 보고서 생성"""
        
        if not self.compatibility_results:
            self.check_all_compatibility()
        
        report = []
        report.append("# 원본 프로젝트 호환성 보고서")
        report.append(f"생성 시간: {self._get_timestamp()}")
        report.append("")
        
        # 전체 평가
        overall = self.compatibility_results.get("overall_compatibility", {})
        report.append(f"## 전체 호환성: {overall.get('status', 'unknown')}")
        report.append(f"호환성 점수: {overall.get('score', 0)}/100")
        report.append("")
        
        # 상세 결과
        for check_name, check_result in self.compatibility_results.items():
            if check_name == "overall_compatibility":
                continue
            
            report.append(f"### {check_name}")
            report.append(f"상태: {check_result.get('status', 'unknown')}")
            
            if check_result.get("issues"):
                report.append("이슈:")
                for issue in check_result["issues"]:
                    report.append(f"- {issue}")
            
            if check_result.get("details"):
                report.append("상세:")
                for key, value in check_result["details"].items():
                    report.append(f"- {key}: {value}")
            
            report.append("")
        
        # 통합 계획
        plan = self.get_integration_plan()
        if plan["priority_tasks"]:
            report.append("## 우선 과업")
            for task in plan["priority_tasks"]:
                report.append(f"- {task}")
            report.append("")
        
        if plan["blocking_issues"]:
            report.append("## 차단 이슈")
            for issue in plan["blocking_issues"]:
                report.append(f"- {issue}")
            report.append("")
        
        return "\n".join(report)
    
    def _get_timestamp(self) -> str:
        """타임스탬프 생성"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
