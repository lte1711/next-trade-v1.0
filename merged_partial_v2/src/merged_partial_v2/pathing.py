"""Path helpers that work in both source and frozen executable modes."""

from __future__ import annotations

import sys
from pathlib import Path


def install_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def resource_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass).resolve()
    return install_root()


def merged_root() -> Path:
    return install_root()


def launcher_root(script_file: str) -> Path:
    if getattr(sys, "frozen", False):
        return install_root()
    return Path(script_file).resolve().parent


def resolve_resource(relative_path: str) -> Path:
    return resource_root() / relative_path
