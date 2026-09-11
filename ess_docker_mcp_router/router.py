import json
from pathlib import Path


def load_profile(path):
    return json.loads(Path(path).read_text())


def load_policy(path):
    return json.loads(Path(path).read_text())


def _deny(reason):
    return {
        "decision": "DENY",
        "reason": reason,
        "read_only": True,
        "external_actuation": False,
    }


def route_request(request, profile, policy):
    if not isinstance(request, dict):
        return _deny("INVALID_REQUEST")

    domain = request.get("domain")
    intent = request.get("intent")
    routes = policy.get("routes", {})
    allowed_intents = set(policy.get("allowed_intents", []))
    forbidden_intents = set(policy.get("forbidden_intents", []))
    excluded = set(policy.get("excluded_surfaces", []))

    if domain not in routes:
        return _deny("UNKNOWN_DOMAIN")
    if intent in forbidden_intents:
        return _deny("FORBIDDEN_INTENT")
    if intent not in allowed_intents:
        return _deny("INTENT_NOT_ALLOWLISTED")

    expected = routes[domain]
    surface = expected["surface"]
    tool = expected["tool"]
    transport = expected["transport"]

    if surface in excluded:
        return _deny("HOLD_SURFACE")

    authoritative = {s["name"]: s for s in profile.get("surfaces", [])}.get(surface)
    if authoritative is None:
        return _deny("SURFACE_NOT_IN_AUTHORITY")
    if authoritative.get("tool") != tool or authoritative.get("transport") != transport:
        return _deny("AUTHORITY_MISMATCH")

    requested_surface = request.get("requested_surface")
    if requested_surface is not None and requested_surface != surface:
        return _deny("WRONG_ROUTE")

    requested_tool = request.get("requested_tool")
    if requested_tool is not None and requested_tool != tool:
        return _deny("WRONG_TOOL")

    requested_transport = request.get("requested_transport")
    if requested_transport is not None and requested_transport != transport:
        return _deny("TRANSPORT_MISMATCH")

    result = {
        "decision": "ALLOW",
        "reason": "ALLOWLIST_MATCH",
        "surface": surface,
        "tool": tool,
        "transport": transport,
        "read_only": True,
        "external_actuation": False,
    }
    if "image_digest" in authoritative:
        result["image_digest"] = authoritative["image_digest"]
    return result
