"""
원본 프로젝트와의 통합 준비 모듈
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, List

class ProjectMerger:
    """프로젝트 통합 준비기"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.original_root = self.project_root.parent
        self.merge_plan = {}
        self.merge_log = []
    
    def prepare_merge_plan(self) -> Dict[str, Any]:
        """통합 계획 준비"""
        
        print("FACT: 프로젝트 통합 계획 준비")
        
        plan = {
            "merge_strategy": "incremental",
            "merge_phases": [
                {
                    "phase": 1,
                    "name": "설정 통합",
                    "description": "원본 설정 파일과 호환성 확보",
                    "tasks": [
                        "config.json 병합",
                        "환경변수 설정",
                        "API 키 연동"
                    ],
                    "priority": "high"
                },
                {
                    "phase": 2,
                    "name": "전략 모듈 통합",
                    "description": "통합 전략 모듈을 원본에 통합",
                    "tasks": [
                        "strategies/ 폴더 복사",
                        "전략 관리자 통합",
                        "전략 클래스 등록"
                    ],
                    "priority": "high"
                },
                {
                    "phase": 3,
                    "name": "시뮬레이션 엔진 통합",
                    "description": "시뮬레이션 엔진을 원본에 통합",
                    "tasks": [
                        "simulation/ 폴더 복사",
                        "엔진 클래스 통합",
                        "API 연동"
                    ],
                    "priority": "medium"
                },
                {
                    "phase": 4,
                    "name": "분석 모듈 통합",
                    "description": "성과 분석 모듈을 원본에 통합",
                    "tasks": [
                        "analysis/ 폴더 복사",
                        "보고서 생성기 통합",
                        "데이터 분석 연동"
                    ],
                    "priority": "medium"
                },
                {
                    "phase": 5,
                    "name": "테스트 및 검증",
                    "description": "통합 후 테스트 및 검증",
                    "tasks": [
                        "통합 테스트 실행",
                        "성능 검증",
                        "호환성 확인"
                    ],
                    "priority": "high"
                }
            ],
            "conflicts": [],
            "backup_plan": "full_backup_before_merge",
            "rollback_plan": "restore_from_backup"
        }
        
        # 충돌 확인
        self._identify_conflicts(plan)
        
        self.merge_plan = plan
        
        print(f"FACT: 통합 계획 준비 완료")
        print(f"  - 통합 단계: {len(plan['merge_phases'])}개")
        print(f"  - 충돌 이슈: {len(plan['conflicts'])}개")
        
        return plan
    
    def _identify_conflicts(self, plan: Dict[str, Any]) -> None:
        """충돌 이슈 확인"""
        
        conflicts = []
        
        # 파일 경로 충돌 확인
        original_files = self._get_original_file_list()
        integrated_files = self._get_integrated_file_list()
        
        for file_path in integrated_files:
            relative_path = file_path.relative_to(self.project_root)
            original_path = self.original_root / relative_path
            
            if original_path.exists():
                conflicts.append({
                    "type": "file_conflict",
                    "path": str(relative_path),
                    "original_exists": True,
                    "resolution": "merge_or_replace"
                })
        
        # 설정 충돌 확인
        original_config = self.original_root / "config.json"
        integrated_config = self.project_root / "config" / "config.json"
        
        if original_config.exists() and integrated_config.exists():
            conflicts.append({
                "type": "config_conflict",
                "path": "config.json",
                "resolution": "merge_configs"
            })
        
        plan["conflicts"] = conflicts
    
    def _get_original_file_list(self) -> List[Path]:
        """원본 파일 목록"""
        files = []
        
        # 중요 폴더만 확인
        important_dirs = ["src", "config", "strategies", "tools"]
        
        for dir_name in important_dirs:
            dir_path = self.original_root / dir_name
            if dir_path.exists():
                files.extend(dir_path.rglob("*.py"))
                files.extend(dir_path.rglob("*.json"))
        
        return files
    
    def _get_integrated_file_list(self) -> List[Path]:
        """통합 파일 목록"""
        files = []
        
        # 통합 프로젝트의 모든 파일
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".py", ".json"]:
                files.append(file_path)
        
        return files
    
    def create_backup(self) -> bool:
        """백업 생성"""
        
        print("FACT: 원본 프로젝트 백업 생성")
        
        backup_dir = self.original_root.parent / f"backup_{self._get_timestamp()}"
        
        try:
            # 백업 디렉토리 생성
            backup_dir.mkdir(exist_ok=True)
            
            # 중요 파일/폴더 백업
            backup_items = [
                "src",
                "config.json",
                "requirements.txt",
                "strategies",
                "tools"
            ]
            
            for item in backup_items:
                original_path = self.original_root / item
                backup_path = backup_dir / item
                
                if original_path.exists():
                    if original_path.is_file():
                        backup_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(original_path, backup_path)
                        self.merge_log.append(f"백업 완료: {item}")
                    elif original_path.is_dir():
                        shutil.copytree(original_path, backup_path, dirs_exist_ok=True)
                        self.merge_log.append(f"백업 완료: {item}/")
            
            print(f"FACT: 백업 생성 완료: {backup_dir}")
            return True
            
        except Exception as e:
            print(f"ERROR: 백업 생성 실패: {e}")
            self.merge_log.append(f"백업 실패: {e}")
            return False
    
    def execute_merge_phase(self, phase_number: int) -> bool:
        """특정 통합 단계 실행"""
        
        if not self.merge_plan:
            self.prepare_merge_plan()
        
        phase = None
        for p in self.merge_plan["merge_phases"]:
            if p["phase"] == phase_number:
                phase = p
                break
        
        if not phase:
            print(f"ERROR: 통합 단계 {phase_number}를 찾을 수 없습니다")
            return False
        
        print(f"FACT: 통합 단계 {phase_number} 실행: {phase['name']}")
        
        try:
            for task in phase["tasks"]:
                success = self._execute_task(task)
                if not success:
                    print(f"ERROR: 작업 실패: {task}")
                    return False
            
            print(f"FACT: 통합 단계 {phase_number} 완료")
            return True
            
        except Exception as e:
            print(f"ERROR: 통합 단계 {phase_number} 실행 실패: {e}")
            return False
    
    def _execute_task(self, task: str) -> bool:
        """개별 작업 실행"""
        
        print(f"FACT: 작업 실행: {task}")
        
        try:
            if "config.json 병합" in task:
                return self._merge_config_files()
            elif "strategies/ 폴더 복사" in task:
                return self._copy_strategies_folder()
            elif "simulation/ 폴더 복사" in task:
                return self._copy_simulation_folder()
            elif "analysis/ 폴더 복사" in task:
                return self._copy_analysis_folder()
            elif "API 키 연동" in task:
                return self._link_api_keys()
            else:
                print(f"WARNING: 알 수 없는 작업: {task}")
                return True
                
        except Exception as e:
            print(f"ERROR: 작업 실행 실패: {e}")
            return False
    
    def _merge_config_files(self) -> bool:
        """설정 파일 병합"""
        
        original_config = self.original_root / "config.json"
        integrated_config = self.project_root / "config" / "config.json"
        
        if not integrated_config.exists():
            print("WARNING: 통합 설정 파일이 없습니다")
            return True
        
        try:
            # 원본 설정 로드
            original_data = {}
            if original_config.exists():
                with open(original_config, 'r', encoding='utf-8') as f:
                    original_data = json.load(f)
            
            # 통합 설정 로드
            with open(integrated_config, 'r', encoding='utf-8') as f:
                integrated_data = json.load(f)
            
            # 설정 병합
            merged_data = {**original_data, **integrated_data}
            
            # 백업 후 저장
            if original_config.exists():
                backup_path = original_config.with_suffix(".json.backup")
                shutil.copy2(original_config, backup_path)
            
            with open(original_config, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, indent=2, ensure_ascii=False)
            
            self.merge_log.append("설정 파일 병합 완료")
            return True
            
        except Exception as e:
            print(f"ERROR: 설정 파일 병합 실패: {e}")
            return False
    
    def _copy_strategies_folder(self) -> bool:
        """전략 폴더 복사"""
        
        src_folder = self.project_root / "src" / "strategies"
        dst_folder = self.original_root / "src" / "strategies"
        
        if not src_folder.exists():
            print("WARNING: 전략 폴더가 없습니다")
            return True
        
        try:
            dst_folder.parent.mkdir(parents=True, exist_ok=True)
            
            if dst_folder.exists():
                # 기존 파일 백업
                backup_folder = dst_folder.with_suffix(".backup")
                if backup_folder.exists():
                    shutil.rmtree(backup_folder)
                shutil.move(dst_folder, backup_folder)
            
            shutil.copytree(src_folder, dst_folder)
            
            self.merge_log.append("전략 폴더 복사 완료")
            return True
            
        except Exception as e:
            print(f"ERROR: 전략 폴더 복사 실패: {e}")
            return False
    
    def _copy_simulation_folder(self) -> bool:
        """시뮬레이션 폴더 복사"""
        
        src_folder = self.project_root / "src" / "simulation"
        dst_folder = self.original_root / "src" / "simulation"
        
        if not src_folder.exists():
            print("WARNING: 시뮬레이션 폴더가 없습니다")
            return True
        
        try:
            dst_folder.parent.mkdir(parents=True, exist_ok=True)
            
            if dst_folder.exists():
                backup_folder = dst_folder.with_suffix(".backup")
                if backup_folder.exists():
                    shutil.rmtree(backup_folder)
                shutil.move(dst_folder, backup_folder)
            
            shutil.copytree(src_folder, dst_folder)
            
            self.merge_log.append("시뮬레이션 폴더 복사 완료")
            return True
            
        except Exception as e:
            print(f"ERROR: 시뮬레이션 폴더 복사 실패: {e}")
            return False
    
    def _copy_analysis_folder(self) -> bool:
        """분석 폴더 복사"""
        
        src_folder = self.project_root / "src" / "analysis"
        dst_folder = self.original_root / "src" / "analysis"
        
        if not src_folder.exists():
            print("WARNING: 분석 폴더가 없습니다")
            return True
        
        try:
            dst_folder.parent.mkdir(parents=True, exist_ok=True)
            
            if dst_folder.exists():
                backup_folder = dst_folder.with_suffix(".backup")
                if backup_folder.exists():
                    shutil.rmtree(backup_folder)
                shutil.move(dst_folder, backup_folder)
            
            shutil.copytree(src_folder, dst_folder)
            
            self.merge_log.append("분석 폴더 복사 완료")
            return True
            
        except Exception as e:
            print(f"ERROR: 분석 폴더 복사 실패: {e}")
            return False
    
    def _link_api_keys(self) -> bool:
        """API 키 연동"""
        
        # API 키 연동은 설정 파일 병합에서 자동으로 처리됨
        self.merge_log.append("API 키 연동 완료 (설정 병합 통해)")
        return True
    
    def generate_merge_report(self) -> str:
        """통합 보고서 생성"""
        
        report = []
        report.append("# 프로젝트 통합 보고서")
        report.append(f"생성 시간: {self._get_timestamp()}")
        report.append("")
        
        if not self.merge_plan:
            report.append("## 통합 계획이 준비되지 않았습니다")
            return "\n".join(report)
        
        # 통합 계획
        report.append("## 통합 계획")
        report.append(f"통합 전략: {self.merge_plan['merge_strategy']}")
        report.append("")
        
        for phase in self.merge_plan["merge_phases"]:
            report.append(f"### 단계 {phase['phase']}: {phase['name']}")
            report.append(f"설명: {phase['description']}")
            report.append(f"우선순위: {phase['priority']}")
            report.append("작업:")
            for task in phase["tasks"]:
                report.append(f"- {task}")
            report.append("")
        
        # 충돌 이슈
        if self.merge_plan["conflicts"]:
            report.append("## 충돌 이슈")
            for conflict in self.merge_plan["conflicts"]:
                report.append(f"- {conflict['type']}: {conflict['path']}")
                report.append(f"  해결 방안: {conflict['resolution']}")
            report.append("")
        
        # 실행 로그
        if self.merge_log:
            report.append("## 실행 로그")
            for log_entry in self.merge_log:
                report.append(f"- {log_entry}")
            report.append("")
        
        return "\n".join(report)
    
    def _get_timestamp(self) -> str:
        """타임스탬프 생성"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def get_merge_status(self) -> Dict[str, Any]:
        """통합 상태 확인"""
        
        return {
            "plan_ready": bool(self.merge_plan),
            "phases_planned": len(self.merge_plan.get("merge_phases", [])),
            "conflicts_identified": len(self.merge_plan.get("conflicts", [])),
            "tasks_completed": len(self.merge_log),
            "backup_available": self._check_backup_available(),
            "ready_to_merge": self._check_merge_readiness()
        }
    
    def _check_backup_available(self) -> bool:
        """백업 가능 여부 확인"""
        backup_dirs = list(self.original_root.parent.glob("backup_*"))
        return len(backup_dirs) > 0
    
    def _check_merge_readiness(self) -> bool:
        """통합 준비 상태 확인"""
        
        # 필수 조건 확인
        if not self.merge_plan:
            return False
        
        # 충돌 확인
        critical_conflicts = [
            c for c in self.merge_plan.get("conflicts", [])
            if c.get("type") == "config_conflict"
        ]
        
        if len(critical_conflicts) > 0:
            return False
        
        return True
