"""Local Binance testnet bridge copied into the merged workspace."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlencode

import requests


def _merged_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_local_config() -> Dict[str, Any]:
    config_path = _merged_root() / "config.json"
    if not config_path.exists():
        return {
            "exchange_base_url": "https://demo-fapi.binance.com",
            "api_key_env": "BINANCE_TESTNET_KEY_PLACEHOLDER",
            "api_secret_env": "BINANCE_TESTNET_SECRET_PLACEHOLDER",
            "recv_window_ms": 5000,
            "default_symbol_count": 10,
        }
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _resolve_api_base() -> str:
    config = _load_local_config()
    return str(config.get("exchange_base_url", "https://demo-fapi.binance.com")).rstrip("/")


def _resolve_credentials() -> tuple[str, str]:
    config = _load_local_config()
    api_key_env = str(config.get("api_key_env", "BINANCE_TESTNET_KEY_PLACEHOLDER"))
    api_secret_env = str(config.get("api_secret_env", "BINANCE_TESTNET_SECRET_PLACEHOLDER"))
    return os.getenv(api_key_env, "").strip(), os.getenv(api_secret_env, "").strip()


def _get_server_time_ms(base_url: str) -> int:
    response = requests.get(f"{base_url}/fapi/v1/time", timeout=5)
    response.raise_for_status()
    payload = response.json()
    return int(payload["serverTime"])


def _signed_request(
    *,
    method: str,
    path: str,
    params: Dict[str, Any] | None = None,
    require_credentials: bool = True,
) -> Dict[str, Any] | list[Any]:
    base_url = _resolve_api_base()
    params = dict(params or {})

    if require_credentials:
        api_key, api_secret = _resolve_credentials()
        if not api_key or not api_secret:
            raise RuntimeError("Missing testnet credentials for private request")

        if "timestamp" not in params:
            params["timestamp"] = str(_get_server_time_ms(base_url))
        if "recvWindow" not in params:
            params["recvWindow"] = str(_load_local_config().get("recv_window_ms", 5000))

        query_string = urlencode(params)
        signature = hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        query_string = f"{query_string}&signature={signature}" if query_string else f"signature={signature}"
        url = f"{base_url}{path}?{query_string}"
        response = requests.request(
            method,
            url,
            headers={"X-MBX-APIKEY": api_key, "Content-Type": "application/x-www-form-urlencoded"},
            timeout=12,
        )
    else:
        query_string = urlencode(params)
        url = f"{base_url}{path}"
        if query_string:
            url = f"{url}?{query_string}"
        response = requests.request(method, url, timeout=12)

    response.raise_for_status()
    return response.json()


def get_account_snapshot() -> Dict[str, Any]:
    """Return a lightweight account snapshot from Binance futures testnet."""
    try:
        payload = _signed_request(method="GET", path="/fapi/v2/account")
    except Exception as exc:
        return {
            "ok": False,
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": "merged_partial_v2",
            "error": str(exc),
        }

    return {
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": "merged_partial_v2",
        "account_equity": float(payload.get("totalMarginBalance", 0.0) or 0.0),
        "wallet_balance": float(payload.get("totalWalletBalance", 0.0) or 0.0),
        "unrealized_pnl": float(payload.get("totalUnrealizedProfit", 0.0) or 0.0),
        "raw": payload,
    }


def get_positions_snapshot() -> Dict[str, Any]:
    """Return current futures position-risk rows from Binance testnet."""
    try:
        payload = _signed_request(method="GET", path="/fapi/v2/positionRisk")
    except Exception as exc:
        return {
            "ok": False,
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": "merged_partial_v2",
            "positions": [],
            "error": str(exc),
        }

    positions = []
    if isinstance(payload, list):
        for row in payload:
            if not isinstance(row, dict):
                continue
            positions.append(
                {
                    "symbol": str(row.get("symbol", "")),
                    "positionAmt": str(row.get("positionAmt", "")),
                    "entryPrice": str(row.get("entryPrice", "")),
                    "markPrice": str(row.get("markPrice", "")),
                    "unRealizedProfit": str(row.get("unRealizedProfit", "")),
                    "positionSide": str(row.get("positionSide", "")),
                    "leverage": str(row.get("leverage", "")),
                    "marginType": str(row.get("marginType", "")),
                    "liquidationPrice": str(row.get("liquidationPrice", "")),
                    "updateTime": str(row.get("updateTime", "")),
                }
            )

    return {
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": "merged_partial_v2",
        "positions": positions,
    }


def submit_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Submit a minimal futures order directly through the merged workspace bridge."""
    api_key, api_secret = _resolve_credentials()
    if not api_key or not api_secret:
        raise RuntimeError("Missing testnet credentials for order submission")

    symbol = str(payload.get("symbol", "")).upper().strip()
    side = str(payload.get("side", "")).upper().strip()
    order_type = str(payload.get("type", "MARKET")).upper().strip() or "MARKET"
    quantity = float(payload.get("qty", payload.get("quantity", 0.0)))
    price = payload.get("price")
    reduce_only = bool(payload.get("reduceOnly", False))
    dry_run = bool(payload.get("dry_run", False))
    trace_id = str(payload.get("trace_id") or f"mpv2-{uuid.uuid4().hex[:12]}")

    if not symbol:
        raise RuntimeError("symbol is required")
    if side not in {"BUY", "SELL"}:
        raise RuntimeError("side must be BUY or SELL")
    if quantity <= 0:
        raise RuntimeError("quantity must be positive")

    base_url = _resolve_api_base()
    if price in (None, ""):
        price_payload = _signed_request(
            method="GET",
            path="/fapi/v1/ticker/price",
            params={"symbol": symbol},
            require_credentials=False,
        )
        price = float(price_payload["price"])
    else:
        price = float(price)

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "submit_called": True,
            "exchange": "BINANCE_TESTNET",
            "trace_id": trace_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "reduceOnly": reduce_only,
            "price": price,
            "status": "FILLED",
            "exchange_order_id": f"dryrun-{trace_id[:12]}",
            "timestamp_used": None,
        }

    params: Dict[str, Any] = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
        "timestamp": str(_get_server_time_ms(base_url)),
        "recvWindow": str(_load_local_config().get("recv_window_ms", 5000)),
        "newClientOrderId": trace_id[:36],
    }
    if reduce_only:
        params["reduceOnly"] = "true"
    if order_type == "LIMIT":
        params["timeInForce"] = "GTC"
        params["price"] = price

    query_string = urlencode(params)
    signature = hmac.new(
        api_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    url = f"{base_url}/fapi/v1/order?{query_string}&signature={signature}"

    response = requests.post(
        url,
        headers={"X-MBX-APIKEY": api_key, "Content-Type": "application/x-www-form-urlencoded"},
        timeout=12,
    )
    response.raise_for_status()
    result = response.json()
    return {
        "ok": True,
        "submit_called": True,
        "exchange": "BINANCE_TESTNET",
        "trace_id": trace_id,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "reduceOnly": reduce_only,
        "price": price,
        "status": result.get("status"),
        "exchange_order_id": result.get("orderId"),
        "raw": result,
        "timestamp_used": params["timestamp"],
        "ts": datetime.now(timezone.utc).isoformat(),
    }
