"""Local Binance testnet bridge copied into the merged workspace."""

from __future__ import annotations

import json
import hashlib
import hmac
import math
import time
import uuid
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlencode

import requests

from merged_partial_v2.exchange.credential_store import resolve_api_base, resolve_credentials, resolve_recv_window_ms
from merged_partial_v2.pathing import merged_root as resolve_merged_root


_SYMBOL_RULES_CACHE: dict[str, Dict[str, float]] = {}


def _merged_root() -> Path:
    return resolve_merged_root()


def _order_log_path() -> Path:
    log_dir = _merged_root() / "order_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "orders.jsonl"


def _append_order_log(record: Dict[str, Any]) -> None:
    with _order_log_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_recent_health_check_summary() -> Dict[str, Any]:
    log_path = _order_log_path()
    if not log_path.exists():
        return {"ok": False, "reason": "no_order_log"}

    lines = log_path.read_text(encoding="utf-8").splitlines()
    health_open = None
    health_close = None
    for raw in reversed(lines):
        try:
            row = json.loads(raw)
        except Exception:
            continue
        trace_id = str(row.get("trace_id", ""))
        if health_close is None and trace_id.startswith("health-close-"):
            health_close = row
        elif health_open is None and trace_id.startswith("health-open-"):
            health_open = row
        if health_open and health_close:
            break

    if not health_open and not health_close:
        return {"ok": False, "reason": "no_health_check_records"}

    return {
        "ok": True,
        "latest_open": health_open,
        "latest_close": health_close,
        "decision_line": (
            f"health-check open={health_open.get('final_status') if health_open else 'n/a'} | "
            f"close={health_close.get('final_status') if health_close else 'n/a'} | "
            f"symbol={health_open.get('symbol') if health_open else health_close.get('symbol') if health_close else 'n/a'}"
        ),
    }


def get_recent_order_failure_summary(max_records: int = 20) -> Dict[str, Any]:
    log_path = _order_log_path()
    if not log_path.exists():
        return {"ok": False, "reason": "no_order_log"}

    failures = []
    for raw in reversed(log_path.read_text(encoding="utf-8").splitlines()):
        try:
            row = json.loads(raw)
        except Exception:
            continue
        if row.get("ok", True) is True:
            continue
        failures.append(row)
        if len(failures) >= max_records:
            break

    if not failures:
        return {
            "ok": True,
            "failure_count": 0,
            "critical_failure_count": 0,
            "retryable_failure_count": 0,
            "categories": {},
            "latest_failure": None,
            "decision_line": "no recent order failures",
        }

    categories: Dict[str, int] = {}
    critical_failure_count = 0
    retryable_failure_count = 0
    for row in failures:
        error_info = dict(row.get("error_info") or {})
        category = str(error_info.get("category") or "unknown")
        categories[category] = categories.get(category, 0) + 1
        if bool(error_info.get("retryable")):
            retryable_failure_count += 1
        else:
            critical_failure_count += 1

    latest_failure = failures[0]
    latest_error_info = dict(latest_failure.get("error_info") or {})
    return {
        "ok": True,
        "failure_count": len(failures),
        "critical_failure_count": critical_failure_count,
        "retryable_failure_count": retryable_failure_count,
        "categories": categories,
        "latest_failure": {
            "ts": latest_failure.get("ts"),
            "symbol": latest_failure.get("symbol"),
            "side": latest_failure.get("side"),
            "category": latest_error_info.get("category"),
            "retryable": latest_error_info.get("retryable"),
            "message": latest_error_info.get("exchange_message"),
            "operator_hint": latest_error_info.get("operator_hint"),
        },
        "decision_line": (
            f"recent failures={len(failures)} | critical={critical_failure_count} | "
            f"retryable={retryable_failure_count}"
        ),
    }


def _map_exchange_error(response: requests.Response | None, exc: Exception) -> Dict[str, Any]:
    code = None
    message = str(exc)
    if response is not None:
        try:
            payload = response.json()
            code = payload.get("code")
            message = payload.get("msg", response.text)
        except Exception:
            message = response.text

    mapped = {
        "code": code,
        "exchange_message": message,
        "category": "unknown",
        "retryable": False,
        "operator_hint": "Check the raw exchange response before retrying.",
    }

    if code == -4164:
        mapped.update(
            {
                "category": "min_notional",
                "retryable": True,
                "operator_hint": "Increase quantity so the order notional is at least the exchange minimum.",
            }
        )
    elif code in {-2019, -2027}:
        mapped.update(
            {
                "category": "insufficient_margin",
                "retryable": False,
                "operator_hint": "Reduce size or free margin before retrying.",
            }
        )
    elif code in {-1111, -4003}:
        mapped.update(
            {
                "category": "quantity_precision",
                "retryable": True,
                "operator_hint": "Normalize the order quantity to the symbol step size and minimum quantity.",
            }
        )
    elif code in {-1021, -1022}:
        mapped.update(
            {
                "category": "signature_or_timestamp",
                "retryable": True,
                "operator_hint": "Retry after refreshing server time and confirming the signing key pair.",
            }
        )
    elif response is not None and response.status_code >= 500:
        mapped.update(
            {
                "category": "exchange_server_error",
                "retryable": True,
                "operator_hint": "Exchange server error. A short retry may succeed.",
            }
        )

    return mapped


def _prefail(
    *,
    trace_id: str,
    symbol: str,
    side: str,
    requested_quantity: float,
    reduce_only: bool,
    category: str,
    operator_hint: str,
    message: str,
    retryable: bool = False,
    price: float | None = None,
    normalization: Dict[str, Any] | None = None,
) -> RuntimeError:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "ok": False,
        "submit_called": False,
        "exchange": "BINANCE_TESTNET",
        "trace_id": trace_id,
        "symbol": symbol,
        "side": side,
        "requested_quantity": requested_quantity,
        "reduceOnly": reduce_only,
        "price": price,
        "normalization": normalization,
        "error_info": {
            "category": category,
            "retryable": retryable,
            "exchange_message": message,
            "operator_hint": operator_hint,
        },
    }
    _append_order_log(record)
    return RuntimeError(f"Order preflight failed [{category}] {message} | hint={operator_hint}")


def _get_server_time_ms(base_url: str) -> int:
    response = requests.get(f"{base_url}/fapi/v1/time", timeout=5)
    response.raise_for_status()
    payload = response.json()
    return int(payload["serverTime"])


def _fetch_symbol_trading_rules(symbol: str) -> Dict[str, float]:
    if symbol in _SYMBOL_RULES_CACHE:
        return dict(_SYMBOL_RULES_CACHE[symbol])

    payload = _signed_request(
        method="GET",
        path="/fapi/v1/exchangeInfo",
        params={"symbol": symbol},
        require_credentials=False,
    )
    symbols = payload.get("symbols", []) if isinstance(payload, dict) else []
    symbol_payload = None
    for item in symbols:
        if not isinstance(item, dict):
            continue
        if str(item.get("symbol", "")).upper() == symbol.upper():
            symbol_payload = item
            break
    if not symbol_payload:
        return {
            "min_qty": 0.0,
            "step_size": 0.0,
            "market_min_qty": 0.0,
            "market_step_size": 0.0,
            "min_notional": 0.0,
            "quantity_precision": 8,
        }

    filters = {item.get("filterType"): item for item in symbol_payload.get("filters", []) if isinstance(item, dict)}
    lot_size = filters.get("LOT_SIZE", {})
    market_lot_size = filters.get("MARKET_LOT_SIZE", {})
    min_notional = filters.get("MIN_NOTIONAL") or filters.get("NOTIONAL") or {}
    quantity_precision_raw = symbol_payload.get("quantityPrecision")
    quantity_precision = 8 if quantity_precision_raw in (None, "") else int(quantity_precision_raw)
    rules = {
        "min_qty": float(lot_size.get("minQty", 0.0) or 0.0),
        "step_size": float(lot_size.get("stepSize", 0.0) or 0.0),
        "market_min_qty": float(market_lot_size.get("minQty", lot_size.get("minQty", 0.0)) or 0.0),
        "market_step_size": float(market_lot_size.get("stepSize", lot_size.get("stepSize", 0.0)) or 0.0),
        "min_notional": float(min_notional.get("notional", min_notional.get("minNotional", 0.0)) or 0.0),
        "quantity_precision": quantity_precision,
    }
    _SYMBOL_RULES_CACHE[symbol] = rules
    return dict(rules)


def _decimal_places(step_size: float) -> int:
    if step_size <= 0:
        return 8
    text = f"{step_size:.12f}".rstrip("0")
    if "." not in text:
        return 0
    return len(text.split(".")[1])


def _format_quantity_for_exchange(quantity: float, step_size: float, quantity_precision: int | None = None) -> str:
    decimals = _decimal_places(step_size)
    if quantity_precision is not None and quantity_precision >= 0:
        decimals = min(decimals, quantity_precision)
    if decimals <= 0:
        return str(int(Decimal(str(quantity)).to_integral_value(rounding=ROUND_DOWN)))
    quantized = Decimal(str(quantity)).quantize(Decimal(f"1e-{decimals}"))
    return format(quantized, f".{decimals}f")


def _normalize_quantity(quantity: float, step_size: float) -> float:
    if step_size <= 0:
        return quantity
    quantity_dec = Decimal(str(quantity))
    step_dec = Decimal(str(step_size))
    steps = (quantity_dec / step_dec).to_integral_value(rounding=ROUND_DOWN)
    normalized = steps * step_dec
    return float(normalized)


def _ceil_to_step(quantity: float, step_size: float) -> float:
    if step_size <= 0:
        return quantity
    quantity_dec = Decimal(str(quantity))
    step_dec = Decimal(str(step_size))
    steps = (quantity_dec / step_dec).to_integral_value(rounding=ROUND_UP)
    normalized = steps * step_dec
    return float(normalized)


def _signed_request(
    *,
    method: str,
    path: str,
    params: Dict[str, Any] | None = None,
    require_credentials: bool = True,
    credential_role: str = "private_read",
) -> Dict[str, Any] | list[Any]:
    base_url = resolve_api_base()
    params = dict(params or {})

    if require_credentials:
        api_key, api_secret = resolve_credentials(credential_role)
        if not api_key or not api_secret:
            raise RuntimeError(f"Missing testnet credentials for role '{credential_role}'")

        if "timestamp" not in params:
            params["timestamp"] = str(_get_server_time_ms(base_url))
        if "recvWindow" not in params:
            params["recvWindow"] = str(resolve_recv_window_ms())

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
        payload = _signed_request(method="GET", path="/fapi/v2/account", credential_role="private_read")
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
        payload = _signed_request(method="GET", path="/fapi/v2/positionRisk", credential_role="private_read")
    except Exception as exc:
        return {
            "ok": False,
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": "merged_partial_v2",
            "positions": [],
            "error": str(exc),
        }

    positions = []
    active_positions = []
    if isinstance(payload, list):
        for row in payload:
            if not isinstance(row, dict):
                continue
            position = {
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
            positions.append(position)
            try:
                if abs(float(position["positionAmt"])) > 0.0:
                    active_positions.append(position)
            except (TypeError, ValueError):
                continue

    return {
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": "merged_partial_v2",
        "positions": positions,
        "position_count": len(positions),
        "active_positions": active_positions,
        "active_position_count": len(active_positions),
    }


def get_order_status(symbol: str, order_id: int | str) -> Dict[str, Any]:
    payload = _signed_request(
        method="GET",
        path="/fapi/v1/order",
        params={"symbol": symbol, "orderId": order_id},
        credential_role="execution",
    )
    return {
        "ok": True,
        "symbol": symbol,
        "order_id": payload.get("orderId"),
        "status": payload.get("status"),
        "executed_qty": payload.get("executedQty"),
        "avg_price": payload.get("avgPrice"),
        "raw": payload,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def wait_for_terminal_order_status(
    symbol: str,
    order_id: int | str,
    *,
    timeout_seconds: float = 6.0,
    poll_interval_seconds: float = 0.75,
) -> Dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_status: Dict[str, Any] | None = None
    while time.time() < deadline:
        last_status = get_order_status(symbol, order_id)
        if last_status.get("status") in {"FILLED", "CANCELED", "REJECTED", "EXPIRED"}:
            return {
                "polled": True,
                "terminal_reached": True,
                **last_status,
            }
        time.sleep(poll_interval_seconds)

    return {
        "polled": True,
        "terminal_reached": False,
        **(last_status or {"ok": False, "symbol": symbol, "order_id": order_id, "status": "UNKNOWN"}),
    }


def submit_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Submit a minimal futures order directly through the merged workspace bridge."""
    api_key, api_secret = resolve_credentials("execution")
    if not api_key or not api_secret:
        raise RuntimeError("Missing testnet execution credentials for order submission")

    symbol = str(payload.get("symbol", "")).upper().strip()
    side = str(payload.get("side", "")).upper().strip()
    order_type = str(payload.get("type", "MARKET")).upper().strip() or "MARKET"
    quantity = float(payload.get("qty", payload.get("quantity", 0.0)))
    price = payload.get("price")
    reduce_only = bool(payload.get("reduceOnly", False))
    dry_run = bool(payload.get("dry_run", False))
    trace_id = str(payload.get("trace_id") or f"mpv2-{uuid.uuid4().hex[:12]}")
    wait_for_fill = bool(payload.get("wait_for_fill", order_type == "MARKET"))
    status_timeout_seconds = float(payload.get("status_timeout_seconds", 6.0))
    status_poll_interval_seconds = float(payload.get("status_poll_interval_seconds", 0.75))
    max_retries = int(payload.get("max_retries", 1))

    if not symbol:
        raise _prefail(
            trace_id=trace_id,
            symbol=symbol,
            side=side,
            requested_quantity=quantity,
            reduce_only=reduce_only,
            category="missing_symbol",
            operator_hint="Provide a valid futures symbol such as BTCUSDT.",
            message="symbol is required",
        )
    if side not in {"BUY", "SELL"}:
        raise _prefail(
            trace_id=trace_id,
            symbol=symbol,
            side=side,
            requested_quantity=quantity,
            reduce_only=reduce_only,
            category="invalid_side",
            operator_hint="Use BUY or SELL only.",
            message="side must be BUY or SELL",
        )
    if quantity <= 0:
        raise _prefail(
            trace_id=trace_id,
            symbol=symbol,
            side=side,
            requested_quantity=quantity,
            reduce_only=reduce_only,
            category="invalid_quantity",
            operator_hint="Provide a quantity greater than zero.",
            message="quantity must be positive",
        )

    base_url = resolve_api_base()
    if price in (None, ""):
        try:
            price_payload = _signed_request(
                method="GET",
                path="/fapi/v1/ticker/price",
                params={"symbol": symbol},
                require_credentials=False,
            )
            price = float(price_payload["price"])
        except Exception as exc:
            response = getattr(exc, "response", None)
            message = response.text if response is not None else str(exc)
            raise _prefail(
                trace_id=trace_id,
                symbol=symbol,
                side=side,
                requested_quantity=quantity,
                reduce_only=reduce_only,
                category="price_lookup_failed",
                operator_hint="Confirm the symbol exists on Binance futures testnet and retry.",
                message=message,
                retryable=False,
            ) from exc
    else:
        price = float(price)

    try:
        rules = _fetch_symbol_trading_rules(symbol)
    except Exception as exc:
        response = getattr(exc, "response", None)
        message = response.text if response is not None else str(exc)
        raise _prefail(
            trace_id=trace_id,
            symbol=symbol,
            side=side,
            requested_quantity=quantity,
            reduce_only=reduce_only,
            category="rule_lookup_failed",
            operator_hint="Confirm exchangeInfo is reachable and the symbol is valid before retrying.",
            message=message,
            retryable=True,
            price=price,
        ) from exc

    active_min_qty = rules["market_min_qty"] if order_type == "MARKET" else rules["min_qty"]
    active_step_size = rules["market_step_size"] if order_type == "MARKET" else rules["step_size"]
    adjusted_quantity = quantity
    if not reduce_only:
        if active_min_qty > 0:
            adjusted_quantity = max(adjusted_quantity, active_min_qty)
        if rules["min_notional"] > 0 and price > 0:
            required_quantity = rules["min_notional"] / price
            adjusted_quantity = max(adjusted_quantity, required_quantity)
        adjusted_quantity = _ceil_to_step(adjusted_quantity, active_step_size)
    elif active_step_size > 0:
        adjusted_quantity = _normalize_quantity(adjusted_quantity, active_step_size)

    if adjusted_quantity <= 0:
        raise _prefail(
            trace_id=trace_id,
            symbol=symbol,
            side=side,
            requested_quantity=quantity,
            reduce_only=reduce_only,
            category="normalized_quantity_invalid",
            operator_hint="Increase quantity or review the symbol step size and minimum notional rules.",
            message="normalized quantity must remain positive",
            retryable=True,
            price=price,
            normalization=rules,
        )

    quantity_for_exchange = _format_quantity_for_exchange(
        adjusted_quantity,
        active_step_size,
        int(rules.get("quantity_precision", 8)),
    )

    if dry_run:
        result = {
            "ok": True,
            "dry_run": True,
            "submit_called": True,
            "exchange": "BINANCE_TESTNET",
            "trace_id": trace_id,
            "symbol": symbol,
            "side": side,
            "quantity": adjusted_quantity,
            "quantity_for_exchange": quantity_for_exchange,
            "requested_quantity": quantity,
            "reduceOnly": reduce_only,
            "price": price,
            "status": "FILLED",
            "exchange_order_id": f"dryrun-{trace_id[:12]}",
            "timestamp_used": None,
            "normalization": rules,
            "final_status": "FILLED",
        }
        _append_order_log(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "ok": True,
                "dry_run": True,
                "symbol": symbol,
                "side": side,
                "requested_quantity": quantity,
                "submitted_quantity": adjusted_quantity,
                "quantity_for_exchange": quantity_for_exchange,
                "reduceOnly": reduce_only,
                "price": price,
                "trace_id": trace_id,
                "status": result["status"],
                "normalization": rules,
            }
        )
        return result

    last_runtime_error: RuntimeError | None = None
    attempt = 0
    while attempt <= max_retries:
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity_for_exchange,
            "timestamp": str(_get_server_time_ms(base_url)),
            "recvWindow": str(resolve_recv_window_ms()),
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

        try:
            response = requests.post(
                url,
                headers={"X-MBX-APIKEY": api_key, "Content-Type": "application/x-www-form-urlencoded"},
                timeout=12,
            )
            response.raise_for_status()
            result = response.json()
            output = {
                "ok": True,
                "submit_called": True,
                "exchange": "BINANCE_TESTNET",
                "trace_id": trace_id,
                "symbol": symbol,
                "side": side,
                "quantity": adjusted_quantity,
                "requested_quantity": quantity,
                "reduceOnly": reduce_only,
                "price": price,
                "status": result.get("status"),
                "exchange_order_id": result.get("orderId"),
                "raw": result,
                "timestamp_used": params["timestamp"],
                "ts": datetime.now(timezone.utc).isoformat(),
                "normalization": rules,
                "attempts_used": attempt + 1,
            }
            if wait_for_fill and output.get("exchange_order_id") is not None:
                output["status_check"] = wait_for_terminal_order_status(
                    symbol,
                    output["exchange_order_id"],
                    timeout_seconds=status_timeout_seconds,
                    poll_interval_seconds=status_poll_interval_seconds,
                )
                output["final_status"] = output["status_check"].get("status", output["status"])
            else:
                output["final_status"] = output["status"]
            _append_order_log(output)
            return output
        except Exception as exc:
            response = getattr(exc, "response", None)
            mapped_error = _map_exchange_error(response, exc)
            should_retry = (
                attempt < max_retries
                and mapped_error.get("retryable", False)
                and mapped_error.get("category") in {"signature_or_timestamp", "exchange_server_error"}
            )
            failure_record = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "ok": False,
                "submit_called": True,
                "exchange": "BINANCE_TESTNET",
                "trace_id": trace_id,
                "symbol": symbol,
                "side": side,
                "requested_quantity": quantity,
                "submitted_quantity": adjusted_quantity,
                "reduceOnly": reduce_only,
                "price": price,
                "status_code": response.status_code if response is not None else None,
                "response_text": response.text if response is not None else str(exc),
                "normalization": rules,
                "error_info": mapped_error,
                "attempt_index": attempt,
                "will_retry": should_retry,
            }
            _append_order_log(failure_record)
            last_runtime_error = RuntimeError(
                f"Order failed [{mapped_error['category']}] code={mapped_error['code']} "
                f"message={mapped_error['exchange_message']} | hint={mapped_error['operator_hint']}"
            )
            if not should_retry:
                raise last_runtime_error from exc
            time.sleep(0.8)
            attempt += 1

    if last_runtime_error is not None:
        raise last_runtime_error
    raise RuntimeError("Order submission failed for an unknown reason")
