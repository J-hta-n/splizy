import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict

import config
from src.lib.receipt_parser.model import RECEIPT_JSON_SCHEMA
from src.lib.receipt_parser.utils import (
    RECEIPT_PARSER_INSTRUCTION,
    detect_image_mime_type,
)


def _extract_text_from_gemini_response(response_payload: Dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    for candidate in candidates:
        content = candidate.get("content") or {}
        for part in content.get("parts") or []:
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()

    prompt_feedback = response_payload.get("promptFeedback") or {}
    block_reason = prompt_feedback.get("blockReason")
    if block_reason:
        raise RuntimeError(
            f"Gemini blocked the receipt parsing request: {block_reason}"
        )

    raise RuntimeError("Gemini returned an empty response")


def extract_receipt_payload_with_gemini_vision(image_bytes: bytes) -> Dict[str, Any]:
    if not config.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured while USE_MOCK_RECEIPT_PARSER is false"
        )

    mime_type = detect_image_mime_type(image_bytes)
    image_base64 = base64.b64encode(image_bytes).decode("ascii")
    model = config.RECEIPT_PARSER_MODEL

    request_payload = {
        "systemInstruction": {
            "parts": [{"text": RECEIPT_PARSER_INSTRUCTION}],
        },
        "contents": [
            {
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": image_base64,
                        }
                    },
                    {
                        "text": "Extract receipt items and totals into the requested schema.",
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseJsonSchema": RECEIPT_JSON_SCHEMA["schema"],
        },
    }

    url = (
        f"{config.GEMINI_BASE_URL}/v1beta/models/"
        f"{urllib.parse.quote(model, safe='')}:generateContent"
    )

    request = urllib.request.Request(
        url,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": config.GEMINI_API_KEY,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=config.RECEIPT_PARSER_TIMEOUT_SEC
        ) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Gemini Vision API request failed with status {exc.code}: {error_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Gemini Vision API request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Gemini Vision API returned invalid JSON") from exc

    content = _extract_text_from_gemini_response(response_payload)
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Gemini Vision API returned non-JSON content: {exc}"
        ) from exc
