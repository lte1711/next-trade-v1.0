from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


APP_NAME = "Merged Partial V2 v1"
INSTALL_ROOT = Path(r"C:\tradev1")
PAYLOAD_DIR_NAME = "package_payload"


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _create_shortcuts(install_root: Path) -> None:
    launcher = install_root / "Launch Merged Partial V2 v1.bat"
    dashboard_launcher = install_root / "Open Merged Partial V2 Dashboard.bat"
    hidden_launcher = install_root / "Launch Merged Partial V2 v1.vbs"
    dashboard_hidden_launcher = install_root / "Open Merged Partial V2 Dashboard.vbs"
    exe_path = install_root / "merged_partial_v2_v1.exe"
    target = hidden_launcher if hidden_launcher.exists() else (launcher if launcher.exists() else exe_path)
    if not target.exists():
        raise RuntimeError(f"Installed executable was not found: {exe_path}")

    desktop = Path.home() / "Desktop" / "Merged Partial V2 v1.lnk"
    desktop_dashboard = Path.home() / "Desktop" / "Merged Partial V2 Dashboard.lnk"
    start_menu_dir = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Merged Partial V2"
    start_menu_dir.mkdir(parents=True, exist_ok=True)
    start_menu = start_menu_dir / "Merged Partial V2 v1.lnk"
    start_menu_dashboard = start_menu_dir / "Merged Partial V2 Dashboard.lnk"

    shortcut_ps = f"""
$WshShell = New-Object -ComObject WScript.Shell
$pairs = @(
  @('{desktop}', '{target}', '{install_root}'),
  @('{start_menu}', '{target}', '{install_root}'),
  @('{desktop_dashboard}', '{dashboard_hidden_launcher if dashboard_hidden_launcher.exists() else (dashboard_launcher if dashboard_launcher.exists() else exe_path)}', '{install_root}'),
  @('{start_menu_dashboard}', '{dashboard_hidden_launcher if dashboard_hidden_launcher.exists() else (dashboard_launcher if dashboard_launcher.exists() else exe_path)}', '{install_root}')
)
foreach ($p in $pairs) {{
  $sc = $WshShell.CreateShortcut($p[0])
  $sc.TargetPath = $p[1]
  $sc.WorkingDirectory = $p[2]
  $sc.Description = 'Merged Partial V2 v1 Background Auto Live'
  $sc.Save()
}}
"""
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            shortcut_ps,
        ],
        check=True,
    )


def _copy_env_example(install_root: Path) -> None:
    actual = install_root / ".env.merged_partial_v2"
    if actual.exists():
        return

    candidates = [
        install_root / ".env.merged_partial_v2",
        install_root / "_internal" / ".env.merged_partial_v2",
        install_root / ".env.merged_partial_v2.example",
        install_root / "_internal" / ".env.merged_partial_v2.example",
    ]
    for candidate in candidates:
        if candidate.exists():
            shutil.copy2(candidate, actual)
            return


def install() -> Path:
    bundle_root = _bundle_root()
    payload_root = bundle_root / PAYLOAD_DIR_NAME
    if not payload_root.exists():
        raise RuntimeError(f"Portable payload not found: {payload_root}")

    stage_root = Path(tempfile.mkdtemp(prefix="merged_partial_v2_install_"))
    try:
        shutil.copytree(payload_root, stage_root, dirs_exist_ok=True)

        if INSTALL_ROOT.exists():
            shutil.rmtree(INSTALL_ROOT, ignore_errors=True)
        INSTALL_ROOT.mkdir(parents=True, exist_ok=True)

        for child in stage_root.iterdir():
            target = INSTALL_ROOT / child.name
            if child.is_dir():
                shutil.copytree(child, target, dirs_exist_ok=True)
            else:
                shutil.copy2(child, target)

        _copy_env_example(INSTALL_ROOT)
        _create_shortcuts(INSTALL_ROOT)
        return INSTALL_ROOT
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)


def main() -> int:
    try:
        install_root = install()
    except Exception as exc:
        print(f"[installer] failed: {exc}", file=sys.stderr)
        return 1

    print(f"{APP_NAME} installation completed: {install_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
