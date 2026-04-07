import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List

import config
from src.lib.logger import get_logger
from src.lib.receipt_parser.model import Receipt

logger = get_logger(__name__)

RECEIPT_PARSER_INSTRUCTION = (
    "You extract line items and totals from noisy restaurant receipts. "
    "Return JSON only that matches the schema. "
    "Rules: parse bilingual or multilingual receipts, keep item names concise and human readable, "
    "ignore notes like 'less sugar' or 'serve first/later' unless they are chargeable items, "
    "set quantity and subtotal per line item, and map currency to ISO code when obvious (for S$ use SGD). "
    "If service charge or GST/tax is missing, set 0."
)

_USAGE_FILE_LOCK = threading.Lock()


def to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        cleaned = str(value).replace(",", "").strip()
        return float(cleaned)
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: int = 1) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return max(1, value)
    try:
        return max(1, int(float(str(value).strip())))
    except (TypeError, ValueError):
        return default


def empty_receipt() -> Receipt:
    return Receipt(
        items=[],
        subtotal=0.0,
        service_charge=0.0,
        gst=0.0,
        total=0.0,
        currency="SGD",
    )


def normalize_receipt_payload(payload: Dict[str, Any]) -> Receipt:
    normalized_items: List[Dict[str, Any]] = []
    raw_items = payload.get("items") or []

    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        name = str(raw_item.get("name") or "").strip()
        if not name:
            continue
        subtotal = to_float(raw_item.get("subtotal"), default=-1)
        if subtotal < 0:
            continue
        normalized_items.append(
            {
                "name": name,
                "quantity": to_int(raw_item.get("quantity"), default=1),
                "subtotal": subtotal,
            }
        )

    subtotal = to_float(payload.get("subtotal"), default=0.0)
    service_charge = to_float(payload.get("service_charge"), default=0.0)
    gst = to_float(payload.get("gst"), default=0.0)
    total = to_float(payload.get("total"), default=0.0)

    if subtotal <= 0 and normalized_items:
        subtotal = round(sum(item["subtotal"] for item in normalized_items), 2)
    if total <= 0:
        total = round(subtotal + service_charge + gst, 2)

    currency = str(payload.get("currency") or "SGD").strip().upper()
    if not currency:
        currency = "SGD"

    return Receipt(
        items=normalized_items,
        subtotal=subtotal,
        service_charge=service_charge,
        gst=gst,
        total=total,
        currency=currency,
    )


def detect_image_mime_type(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if len(image_bytes) >= 12 and image_bytes[4:12] in (b"ftypheic", b"ftypheif"):
        return "image/heic"
    return "image/jpeg"


def usage_month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def usage_file_path() -> str:
    configured = (config.RECEIPT_PARSER_USAGE_FILE_PATH or "").strip()
    path = configured or ".receipt_parser_usage.json"
    if os.path.isabs(path):
        return path
    return os.path.abspath(path)


def load_usage_state(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as file_handle:
            state = json.load(file_handle)
        if isinstance(state, dict):
            return state
        return {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_usage_state(path: str, state: Dict[str, Any]) -> None:
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as file_handle:
        json.dump(state, file_handle)
    os.replace(tmp_path, path)


def enforce_monthly_quota() -> None:
    monthly_limit = max(0, int(config.RECEIPT_PARSER_MONTHLY_LIMIT))
    if monthly_limit == 0:
        return

    month = usage_month_key()
    path = usage_file_path()

    with _USAGE_FILE_LOCK:
        state = load_usage_state(path)
        if state.get("month") != month:
            state = {"month": month, "count": 0}

        try:
            count = int(state.get("count", 0))
        except (TypeError, ValueError):
            count = 0

        if count >= monthly_limit:
            raise RuntimeError(
                "Monthly receipt parser quota reached "
                f"({monthly_limit}/{monthly_limit}). "
                "Increase RECEIPT_PARSER_MONTHLY_LIMIT or wait for next month."
            )

        state["count"] = count + 1
        save_usage_state(path, state)

    logger.info(
        "Receipt parser monthly quota usage: %s/%s",
        state["count"],
        monthly_limit,
    )
