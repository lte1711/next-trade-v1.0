"""
NT-PATCH-SET-9-001: PERSISTENT_EXECUTION_GUARD
Author: Candy (Constitution v1.2 Compliant)
Purpose: Persistent execution counter guard with stale-lock recovery.
"""

import json
from datetime import datetime
from pathlib import Path
import msvcrt


class ExecutionGuard:
    """Persistent execution guard backed by a small lock file."""

    def __init__(self, storage_path="var/execution_state.json", max_execution_limit=50, stale_reset_minutes=3):
        self.storage_path = Path(storage_path)
        self.storage_path = Path(__file__).resolve().parents[1] / self.storage_path
        self.max_execution_limit = max(1, int(max_execution_limit or 1))
        self.stale_reset_minutes = max(1, int(stale_reset_minutes or 1))
        self.counter = self._load_from_disk()

    def _is_stale_locked_state(self, counter, last_update_raw):
        if int(counter or 0) < self.max_execution_limit:
            return False
        if not last_update_raw:
            return False
        try:
            last_update = datetime.fromisoformat(str(last_update_raw))
        except Exception:
            return False
        return (datetime.now() - last_update).total_seconds() >= (self.stale_reset_minutes * 60)

    def _load_from_disk(self):
        if not self.storage_path.exists():
            return 0

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            counter = int(data.get("counter", 0) or 0)
            if self._is_stale_locked_state(counter, data.get("last_update")):
                self._save_to_disk(0)
                return 0
            return counter
        except Exception:
            return 0

    def _save_to_disk(self, count):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "counter": int(count),
                        "last_update": datetime.now().isoformat(),
                        "status": "LOCKED" if int(count) >= self.max_execution_limit else "OPEN",
                        "patch_version": "NT-PATCH-SET-9-001",
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as e:
            print(f"EXECUTION_GUARD_SAVE_ERROR: {e}")
            raise RuntimeError("CRITICAL: Cannot save execution state - forcing block")

    def validate_and_lock(self):
        f = None
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            f = open(self.storage_path, "a+", encoding="utf-8")
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            f.seek(0)
            raw = f.read()

            counter = 0
            last_update_raw = None
            if raw.strip():
                try:
                    data = json.loads(raw)
                    counter = int(data.get("counter", 0) or 0)
                    last_update_raw = data.get("last_update")
                except Exception:
                    try:
                        counter = int(raw.strip())
                    except Exception:
                        counter = 0

            if self._is_stale_locked_state(counter, last_update_raw):
                counter = 0

            if counter >= self.max_execution_limit:
                self._save_to_disk(counter)
                return False, "BLOCKED"

            counter += 1
            f.seek(0)
            f.truncate()
            json.dump(
                {
                    "counter": counter,
                    "last_update": datetime.now().isoformat(),
                    "status": "LOCKED" if counter >= self.max_execution_limit else "OPEN",
                    "patch_version": "NT-PATCH-SET-9-001",
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
            f.flush()
            self.counter = counter
            return True, "SUCCESS"
        finally:
            if f:
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    f.close()
                except Exception:
                    pass

    def get_current_state(self):
        self.counter = self._load_from_disk()
        return {
            "counter": self.counter,
            "limit": self.max_execution_limit,
            "status": "LOCKED" if self.counter >= self.max_execution_limit else "OPEN",
            "storage_path": str(self.storage_path),
            "last_update": datetime.now().isoformat(),
            "stale_reset_minutes": self.stale_reset_minutes,
        }

    def reset_state(self):
        if self.storage_path.exists():
            try:
                self.storage_path.unlink()
                self.counter = 0
                return True, "State reset successfully"
            except Exception as e:
                return False, f"Reset failed: {e}"
        return True, "No state file to reset"
