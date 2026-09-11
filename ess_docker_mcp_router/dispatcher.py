import hashlib
import json

from router import route_request


def _canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value):
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def build_receipt(request, route, response=None):
    receipt = {
        "decision": route["decision"],
        "reason": route["reason"],
        "read_only": True,
        "external_actuation": False,
        "request_sha256": _sha256(request),
        "route_sha256": _sha256(route),
    }
    if route["decision"] == "ALLOW":
        receipt.update(
            {
                "surface": route["surface"],
                "tool": route["tool"],
                "transport": route["transport"],
                "response_sha256": _sha256(response),
                "response": response,
            }
        )
        if "image_digest" in route:
            receipt["image_digest"] = route["image_digest"]
    return receipt


def dispatch_request(request, profile, policy, executor):
    route = route_request(request, profile, policy)
    if route["decision"] != "ALLOW":
        return build_receipt(request, route)
    response = executor(route, request.get("arguments", {}))
    return build_receipt(request, route, response)


def receipts_equal(first, second):
    return _canonical_bytes(first) == _canonical_bytes(second)
