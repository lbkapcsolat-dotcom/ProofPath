IDENTITY_FIELDS = ("boot_id", "product_uuid", "runner_name")


def _identity_distinct(a, b):
    ia = a.get("identity") or {}
    ib = b.get("identity") or {}
    return all(ia.get(k) and ib.get(k) and ia.get(k) != ib.get(k) for k in IDENTITY_FIELDS)


def build_cross_host_coverage(profile, host_a, host_b):
    surfaces = profile.get("surfaces") or []
    authority = {s["name"]: s for s in surfaces}
    if len(surfaces) != 13 or len(authority) != 13:
        raise ValueError("EXACT_13_SURFACE_AUTHORITY_REQUIRED")

    gateway_count = sum(1 for s in surfaces if s.get("transport") == "gateway-profile")
    direct_count = sum(1 for s in surfaces if s.get("transport") == "direct-image")
    if gateway_count != 11 or direct_count != 2:
        raise ValueError("EXPECTED_11_GATEWAY_2_DIRECT_TRANSPORT_SPLIT")

    aresults = host_a.get("results") or {}
    bresults = host_b.get("results") or {}
    rows = []

    for name in sorted(authority):
        expected_transport = authority[name].get("transport")
        a = aresults.get(name)
        b = bresults.get(name)
        status = "CROSS_HOST_EQUAL"
        reasons = []

        if a is None or b is None:
            status = "MISSING_SURFACE"
            reasons.append("HOST_RESULT_MISSING")
        elif a.get("transport") != expected_transport or b.get("transport") != expected_transport:
            status = "TRANSPORT_AUTHORITY_MISMATCH"
            reasons.append("TRANSPORT_DOES_NOT_MATCH_PROFILE")
        elif a.get("status") != "LIVE_PASS" or b.get("status") != "LIVE_PASS":
            status = "HOST_CALL_HOLD"
            reasons.append("LIVE_PASS_REQUIRED_ON_BOTH_HOSTS")
        elif a.get("request_sha256") != b.get("request_sha256") or a.get("route_sha256") != b.get("route_sha256"):
            status = "REQUEST_ROUTE_DRIFT"
            reasons.append("REQUEST_OR_ROUTE_SHA_MISMATCH")
        elif a.get("response_sha256") != b.get("response_sha256") or a.get("response") != b.get("response"):
            status = "CROSS_HOST_CONTENT_DRIFT"
            reasons.append("PROFESSIONAL_RESPONSE_MISMATCH")

        rows.append({
            "surface": name,
            "transport": expected_transport,
            "status": status,
            "reasons": reasons,
        })

    equal_count = sum(1 for r in rows if r["status"] == "CROSS_HOST_EQUAL")
    distinct = _identity_distinct(host_a, host_b)
    return {
        "surface_count": 13,
        "gateway_profile_count": gateway_count,
        "direct_image_count": direct_count,
        "equal_surface_count": equal_count,
        "all_surfaces_equal": equal_count == 13 and distinct,
        "distinct_host_identity": distinct,
        "identity_authority_fields": list(IDENTITY_FIELDS),
        "rows": rows,
    }
