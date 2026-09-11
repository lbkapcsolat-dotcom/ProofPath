import json
import re

_TIMING_SURFACES = {"hugging-face", "astro-docs", "javadocs", "maven-tools-mcp"}
_TIMING_PREFIX = re.compile(r"^Tool call took: [0-9]+(?:\.[0-9]+)?(?:ms|s)\n")


def _normalize_text(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def canonicalize_surface_response(surface, text):
    text = _normalize_text(text)

    if surface in _TIMING_SURFACES:
        return _TIMING_PREFIX.sub("", text, count=1)

    if surface == "context7":
        parts = [part.strip() for part in text.strip().split("----------") if part.strip()]
        return "\n----------\n".join(sorted(parts))

    if surface == "ros2":
        try:
            value = json.loads(text)
        except (TypeError, ValueError, json.JSONDecodeError):
            return text
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            return text
        return json.dumps(sorted(value), ensure_ascii=False, separators=(",", ":"))

    # Fail closed for all other surfaces, including gemini-api-docs.
    return text


def diagnose_pair(surface, a, b):
    a = _normalize_text(a)
    b = _normalize_text(b)
    if a == b:
        return {"classification": "RAW_EQUAL", "equal_after_bounded_normalization": True}

    ca = canonicalize_surface_response(surface, a)
    cb = canonicalize_surface_response(surface, b)
    if ca == cb:
        if surface in _TIMING_SURFACES:
            classification = "BOUNDED_TIMING_NOISE"
        elif surface == "context7":
            classification = "BOUNDED_RECORD_ORDER_NOISE"
        elif surface == "ros2":
            classification = "BOUNDED_LIST_ORDER_NOISE"
        else:
            classification = "BOUNDED_NORMALIZED_EQUAL"
        return {"classification": classification, "equal_after_bounded_normalization": True}

    return {"classification": "TRUE_CONTENT_DRIFT", "equal_after_bounded_normalization": False}
