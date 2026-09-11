from drift_normalization import diagnose_pair


_IDENTITY_FIELDS = ("boot_id", "product_uuid", "runner_name")


def _distinct_hosts(a, b):
    ia = a.get("identity", {})
    ib = b.get("identity", {})
    return all(ia.get(k) and ib.get(k) and ia[k] != ib[k] for k in _IDENTITY_FIELDS)


def build_post_quarantine_cross_host_matrix(profile, policy, host_a, host_b):
    surfaces = profile.get("surfaces", [])
    authority = {s["name"]: s for s in surfaces}
    quarantined_domains = policy.get("quarantined_domains", {})
    routes = policy.get("routes", {})

    quarantined_surfaces = sorted(
        {
            q.get("surface") or routes.get(domain, {}).get("surface")
            for domain, q in quarantined_domains.items()
        }
        - {None}
    )
    routable_surfaces = sorted(
        {
            route.get("surface")
            for domain, route in routes.items()
            if domain not in quarantined_domains and route.get("surface")
        }
    )

    rows = []
    for surface in routable_surfaces:
        expected = authority.get(surface, {})
        a = host_a.get("results", {}).get(surface)
        b = host_b.get("results", {}).get(surface)
        reasons = []

        if not expected:
            status = "AUTHORITY_MISSING_HOLD"
            reasons.append("SURFACE_NOT_IN_AUTHORITY")
        elif a is None or b is None:
            status = "MISSING_SURFACE_HOLD"
            reasons.append("HOST_RESULT_MISSING")
        elif a.get("transport") != expected.get("transport") or b.get("transport") != expected.get("transport"):
            status = "TRANSPORT_MISMATCH_HOLD"
            reasons.append("TRANSPORT_AUTHORITY_MISMATCH")
        elif a.get("status") != "LIVE_PASS" or b.get("status") != "LIVE_PASS":
            status = "LIVE_STATUS_HOLD"
            reasons.append("NON_LIVE_PASS_RESULT")
        elif a.get("request_sha256") != b.get("request_sha256"):
            status = "REQUEST_DRIFT_HOLD"
            reasons.append("REQUEST_SHA_MISMATCH")
        elif a.get("route_sha256") != b.get("route_sha256"):
            status = "ROUTE_DRIFT_HOLD"
            reasons.append("ROUTE_SHA_MISMATCH")
        else:
            diagnosis = diagnose_pair(surface, a.get("response", ""), b.get("response", ""))
            if diagnosis["equal_after_bounded_normalization"]:
                status = "RAW_EQUAL_PASS" if diagnosis["classification"] == "RAW_EQUAL" else "BOUNDED_INVARIANT_PASS"
                reasons.append(diagnosis["classification"])
            else:
                status = "TRUE_CONTENT_DRIFT_HOLD"
                reasons.append(diagnosis["classification"])

        rows.append(
            {
                "surface": surface,
                "transport": expected.get("transport"),
                "status": status,
                "reasons": reasons,
            }
        )

    effective = sum(r["status"] in {"RAW_EQUAL_PASS", "BOUNDED_INVARIANT_PASS"} for r in rows)
    return {
        "authority_surface_count": len(surfaces),
        "routable_surface_count": len(routable_surfaces),
        "quarantined_surfaces": quarantined_surfaces,
        "gateway_profile_count": sum(authority[s].get("transport") == "gateway-profile" for s in routable_surfaces if s in authority),
        "direct_image_count": sum(authority[s].get("transport") == "direct-image" for s in routable_surfaces if s in authority),
        "distinct_host_identity": _distinct_hosts(host_a, host_b),
        "identity_authority_fields": list(_IDENTITY_FIELDS),
        "effective_invariant_count": effective,
        "all_routable_surfaces_invariant": (
            len(surfaces) == 13
            and len(routable_surfaces) == 12
            and quarantined_surfaces == ["gemini-api-docs"]
            and _distinct_hosts(host_a, host_b)
            and effective == len(rows) == 12
        ),
        "rows": rows,
    }
