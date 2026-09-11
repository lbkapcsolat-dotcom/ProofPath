import hashlib
import json
import re

from executor_binding import ExecutorBindingError, validate_execution_trace


class ReceiptBindingError(RuntimeError):
    pass


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha_json(value):
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _require_sha256(name, value):
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ReceiptBindingError(f"INVALID_SHA256:{name}")


def _response_bytes(value):
    if isinstance(value, bytes):
        data = value
    elif isinstance(value, str):
        data = value.encode("utf-8")
    else:
        raise ReceiptBindingError("RESPONSE_NOT_BYTES_OR_TEXT")
    if not data:
        raise ReceiptBindingError("RESPONSE_EMPTY")
    return data


def _verify_self_hash(receipt):
    if not isinstance(receipt, dict):
        raise ReceiptBindingError("RECEIPT_NOT_OBJECT")
    claimed = receipt.get("receipt_sha256")
    _require_sha256("receipt_sha256", claimed)
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    actual = _sha_json(unsigned)
    if claimed != actual:
        raise ReceiptBindingError("RECEIPT_SELF_HASH_MISMATCH")


def build_surface_receipt(
    *,
    request,
    plan,
    trace,
    response_bytes,
    policy_sha256,
    profile_sha256,
    execution_id,
):
    if not isinstance(execution_id, str) or not execution_id.strip():
        raise ReceiptBindingError("EXECUTION_ID_REQUIRED")
    _require_sha256("policy_sha256", policy_sha256)
    _require_sha256("profile_sha256", profile_sha256)
    data = _response_bytes(response_bytes)

    if not plan.get("executor_allowed"):
        raise ReceiptBindingError("EXECUTOR_NOT_AUTHORIZED")
    try:
        binding = validate_execution_trace(plan, trace)
    except ExecutorBindingError as exc:
        raise ReceiptBindingError(str(exc)) from exc
    if trace.get("exit_code") != 0:
        raise ReceiptBindingError("EXECUTOR_EXIT_NONZERO")

    contract = plan["executor_contract"]
    if plan.get("executor_contract_sha256") != _sha_json(contract):
        raise ReceiptBindingError("EXECUTOR_CONTRACT_HASH_MISMATCH")

    transport = contract["transport"]
    if transport == "direct-image":
        response_binding_mode = "EXACT_RESPONSE_SHA_REQUIRED_ON_REPLAY"
    elif transport == "gateway-profile":
        response_binding_mode = "INDIVIDUAL_RESPONSE_SHA_BOUND__CROSS_REPLAY_BYTE_EQUALITY_NOT_REQUIRED"
    else:
        raise ReceiptBindingError("UNSUPPORTED_TRANSPORT")

    receipt = {
        "receipt_version": 1,
        "execution_id": execution_id,
        "request_sha256": _sha_json(request),
        "route_sha256": _sha_json(plan["route"]),
        "executor_contract_sha256": plan["executor_contract_sha256"],
        "executor_trace_binding_sha256": binding["executor_trace_sha256"],
        "executor_trace_full_sha256": _sha_json(trace),
        "policy_sha256": policy_sha256,
        "profile_sha256": profile_sha256,
        "surface": contract["surface"],
        "tool": contract["tool"],
        "transport": transport,
        "arguments_sha256": _sha_json(contract.get("arguments", {})),
        "read_only": contract.get("read_only") is True,
        "external_actuation": contract.get("external_actuation") is True,
        "executor_invoked": trace.get("executor_invoked") is True,
        "executor_exit_code": trace.get("exit_code"),
        "response_sha256": _sha_bytes(data),
        "response_bytes": len(data),
        "response_nonempty": True,
        "response_binding_mode": response_binding_mode,
    }
    if "image_digest" in contract:
        receipt["image_digest"] = contract["image_digest"]
    receipt["receipt_sha256"] = _sha_json(receipt)
    return receipt


def validate_surface_receipt(
    *,
    receipt,
    request,
    plan,
    trace,
    response_bytes,
    policy_sha256,
    profile_sha256,
):
    _verify_self_hash(receipt)
    expected = build_surface_receipt(
        request=request,
        plan=plan,
        trace=trace,
        response_bytes=response_bytes,
        policy_sha256=policy_sha256,
        profile_sha256=profile_sha256,
        execution_id=receipt.get("execution_id"),
    )
    if receipt != expected:
        keys = sorted(set(receipt) | set(expected))
        mismatches = [k for k in keys if receipt.get(k) != expected.get(k)]
        raise ReceiptBindingError("RECEIPT_BINDING_MISMATCH:" + ",".join(mismatches))
    return {
        "receipt_valid": True,
        "receipt_sha256": receipt["receipt_sha256"],
        "surface": receipt["surface"],
        "transport": receipt["transport"],
    }


def compare_independent_replay(primary_receipt, replay_receipt):
    _verify_self_hash(primary_receipt)
    _verify_self_hash(replay_receipt)
    if primary_receipt.get("execution_id") == replay_receipt.get("execution_id"):
        raise ReceiptBindingError("REPLAY_NOT_INDEPENDENT_EXECUTION")

    identity_fields = (
        "receipt_version",
        "request_sha256",
        "route_sha256",
        "executor_contract_sha256",
        "executor_trace_binding_sha256",
        "policy_sha256",
        "profile_sha256",
        "surface",
        "tool",
        "transport",
        "arguments_sha256",
        "read_only",
        "external_actuation",
        "executor_invoked",
        "executor_exit_code",
        "response_binding_mode",
    )
    for field in identity_fields:
        if primary_receipt.get(field) != replay_receipt.get(field):
            raise ReceiptBindingError(f"REPLAY_BINDING_MISMATCH:{field}")
    if primary_receipt.get("image_digest") != replay_receipt.get("image_digest"):
        raise ReceiptBindingError("REPLAY_BINDING_MISMATCH:image_digest")
    if not primary_receipt.get("response_nonempty") or not replay_receipt.get("response_nonempty"):
        raise ReceiptBindingError("REPLAY_RESPONSE_EMPTY")

    response_equal = primary_receipt["response_sha256"] == replay_receipt["response_sha256"]
    transport = primary_receipt["transport"]
    if transport == "direct-image":
        if not response_equal:
            raise ReceiptBindingError("REPLAY_RESPONSE_SHA_MISMATCH")
        response_equivalence = "EXACT_RESPONSE_REPLAY"
    elif transport == "gateway-profile":
        response_equivalence = "RESPONSE_INDIVIDUALLY_BOUND__BYTE_EQUALITY_NOT_REQUIRED"
    else:
        raise ReceiptBindingError("UNSUPPORTED_TRANSPORT")

    return {
        "replay_valid": True,
        "surface": primary_receipt["surface"],
        "transport": transport,
        "response_sha256_equal": response_equal,
        "response_equivalence": response_equivalence,
        "primary_receipt_sha256": primary_receipt["receipt_sha256"],
        "replay_receipt_sha256": replay_receipt["receipt_sha256"],
    }
