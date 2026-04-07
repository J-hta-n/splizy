import base64
import json
from typing import Any, Dict

from openai import OpenAI

import config
from src.lib.receipt_parser.model import RECEIPT_JSON_SCHEMA
from src.lib.receipt_parser.utils import RECEIPT_PARSER_INSTRUCTION


def extract_receipt_payload_with_openai_vision(image_bytes: bytes) -> Dict[str, Any]:
    if not config.OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured while USE_MOCK_RECEIPT_PARSER is false"
        )

    image_base64 = base64.b64encode(image_bytes).decode("ascii")
    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL or None,
        timeout=config.RECEIPT_PARSER_TIMEOUT_SEC,
    )

    response = client.chat.completions.create(
        model=config.RECEIPT_PARSER_MODEL,
        messages=[
            {
                "role": "system",
                "content": RECEIPT_PARSER_INSTRUCTION,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract receipt items and totals into the requested schema.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                        },
                    },
                ],
            },
        ],
        response_format={"type": "json_schema", "json_schema": RECEIPT_JSON_SCHEMA},
        temperature=0,
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Vision API returned an empty response")

    if isinstance(content, list):
        text_chunks = [
            part.get("text", "") for part in content if isinstance(part, dict)
        ]
        content = "\n".join(text_chunks).strip()

    if not isinstance(content, str):
        raise RuntimeError("Vision API response content is not text")

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Vision API returned non-JSON content: {e}") from e
