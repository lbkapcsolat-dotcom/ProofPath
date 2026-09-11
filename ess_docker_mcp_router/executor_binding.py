import hashlib
import json

from router import route_request


class ExecutorBindingError(RuntimeError):
    pass


def _canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value):
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def plan_execution(request, profile, policy):
    route = route_request(request, profile, policy)
    plan = {
        "route": route,
        "executor_allowed": route.get("decision") == "ALLOW",
        "read_only": True,
        "external_actuation": False,
    }
    if not plan["executor_allowed"]:
        return plan

    contract = {
        "surface": route["surface"],
        "tool": route["tool"],
        "transport": route["transport"],
        "arguments": request.get("arguments", {}),
        "read_only": True,
        "external_actuation": False,
    }
    if "image_digest" in route:
        contract["image_digest"] = route["image_digest"]
    plan["executor_contract"] = contract
    plan["executor_contract_sha256"] = _sha256(contract)
    if contract["transport"] == "direct-image":
        plan.update(contract)
    return plan


def validate_execution_trace(plan, trace):
    if not plan.get("executor_allowed"):
        raise ExecutorBindingError("EXECUTOR_NOT_AUTHORIZED")
    if not trace.get("executor_invoked"):
        raise ExecutorBindingError("EXECUTOR_NOT_INVOKED")

    expected = plan["executor_contract"]
    for field in ("surface", "tool", "transport", "arguments", "read_only", "external_actuation"):
        if trace.get(field) != expected.get(field):
            raise ExecutorBindingError(f"EXECUTOR_BINDING_MISMATCH:{field}")
    if "image_digest" in expected and trace.get("image_digest") != expected["image_digest"]:
        raise ExecutorBindingError("EXECUTOR_BINDING_MISMATCH:image_digest")
    return {
        "binding_valid": True,
        "executor_contract_sha256": plan["executor_contract_sha256"],
        "executor_trace_sha256": _sha256({k: trace.get(k) for k in expected}),
    }
