import json
import re


_TOOL_CALL_TIMING_PREFIX = re.compile(r"\ATool call took: [0-9]+(?:\.[0-9]+)?s\n")


def _canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def normalize_tool_response(response):
    return _TOOL_CALL_TIMING_PREFIX.sub("", response, count=1)


def normalize_gateway_receipt(receipt):
    normalized = dict(receipt)
    normalized.pop("runtime_meta", None)
    return normalized


def normalized_receipts_equal(first, second):
    return _canonical_bytes(normalize_gateway_receipt(first)) == _canonical_bytes(normalize_gateway_receipt(second))
