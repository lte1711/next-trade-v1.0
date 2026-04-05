"""Credential loading helpers for merged_partial_v2 role-based API access."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from merged_partial_v2.pathing import (
    install_root as resolve_install_root,
    resource_root as resolve_resource_root,
)


def merged_root() -> Path:
    return resolve_install_root()


@lru_cache(maxsize=1)
def load_local_config() -> dict[str, Any]:
    config_path = resolve_resource_root() / "config.json"
    if not config_path.exists():
        return {
            "exchange_base_url": "https://demo-fapi.binance.com",
            "recv_window_ms": 5000,
            "default_symbol_count": 10,
            "credential_envs": {
                "public_read": {
                    "api_key_env": "BINANCE_TESTNET_READONLY_API_KEY",
                    "api_secret_env": "BINANCE_TESTNET_READONLY_API_SECRET",
                },
                "private_read": {
                    "api_key_env": "BINANCE_TESTNET_ACCOUNT_API_KEY",
                    "api_secret_env": "BINANCE_TESTNET_ACCOUNT_API_SECRET",
                },
                "execution": {
                    "api_key_env": "BINANCE_TESTNET_TRADING_API_KEY",
                    "api_secret_env": "BINANCE_TESTNET_TRADING_API_SECRET",
                },
            },
        }
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_env_file_values() -> dict[str, str]:
    env_path = resolve_install_root() / ".env.merged_partial_v2"
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values


def resolve_api_base() -> str:
    return str(load_local_config().get("exchange_base_url", "https://demo-fapi.binance.com")).rstrip("/")


def resolve_recv_window_ms() -> int:
    return int(load_local_config().get("recv_window_ms", 5000))


def resolve_credential_env_names(role: str) -> tuple[str, str]:
    credential_envs = dict(load_local_config().get("credential_envs", {}))
    role_config = dict(credential_envs.get(role, {}))
    return (
        str(role_config.get("api_key_env", "")).strip(),
        str(role_config.get("api_secret_env", "")).strip(),
    )


def resolve_credentials(role: str) -> tuple[str, str]:
    api_key_env, api_secret_env = resolve_credential_env_names(role)
    env_values = load_env_file_values()
    api_key = os.getenv(api_key_env, env_values.get(api_key_env, "")).strip() if api_key_env else ""
    api_secret = os.getenv(api_secret_env, env_values.get(api_secret_env, "")).strip() if api_secret_env else ""
    return api_key, api_secret


def build_public_headers() -> dict[str, str]:
    api_key, _ = resolve_credentials("public_read")
    return {"X-MBX-APIKEY": api_key} if api_key else {}


def describe_credentials() -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for role in ("public_read", "private_read", "execution"):
        api_key_env, api_secret_env = resolve_credential_env_names(role)
        api_key, api_secret = resolve_credentials(role)
        summary[role] = {
            "api_key_env": api_key_env,
            "api_secret_env": api_secret_env,
            "api_key_loaded": bool(api_key),
            "api_secret_loaded": bool(api_secret),
        }
    return summary
