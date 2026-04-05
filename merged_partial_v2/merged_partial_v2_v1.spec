# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(r"c:\next-trade-ver1.0")
merged_root = project_root / "merged_partial_v2"
src_root = merged_root / "src"
release_root = merged_root / "release"

block_cipher = None

a = Analysis(
    [str(merged_root / "run_merged_partial_v2.py")],
    pathex=[str(src_root), str(merged_root)],
    binaries=[],
    datas=[
        (str(merged_root / "config.json"), "."),
        (str(merged_root / "README.md"), "."),
        (str(merged_root / "SAFE_LIVE_AUTONOMOUS_TRANSITION.md"), "."),
        (str(merged_root / ".env.merged_partial_v2"), "."),
        (str(merged_root / ".env.merged_partial_v2.example"), "."),
        (str(merged_root / "dashboard_assets"), "dashboard_assets"),
        (str(merged_root / "profile_reports" / "remote_profile_metrics.json"), "profile_reports"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="merged_partial_v2_v1",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    version=str(merged_root / "version_info_v1.txt"),
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="merged_partial_v2_v1",
)
