from __future__ import annotations

import json
from pathlib import Path

import router

HERE = Path(__file__).resolve().parent
FIXTURE = json.loads((HERE / "fixtures" / "canary_records.json").read_text(encoding="utf-8"))


def by_id(results):
    return {r["id"]: r for r in results}


def run() -> None:
    assert router.normalize_doi("https://doi.org/10.1111/FAF.70079") == "10.1111/faf.70079"
    assert router.normalize_arxiv("arXiv:2608.13867v1") == "2608.13867"

    groups, alias_map = router.dedupe_records(FIXTURE["records"])
    assert len(groups) == 4, groups

    peer_idx = alias_map["doi:10.1111/faf.70079"]
    peer = groups[peer_idx]
    assert peer["engines"] == ["scholar_gateway", "scispace", "scite"]

    agent_idx = alias_map["arxiv:2608.13867"]
    agent = groups[agent_idx]
    assert agent["engines"] == ["alphaxiv", "sider_openalex"]

    retracted_idx = alias_map["doi:10.1016/s0140-6736(97)11096-0"]
    assert "retracted" in groups[retracted_idx]["editorial_flags"]

    claims = by_id(router.evaluate_claims(FIXTURE))
    assert claims["C1"]["status"] == "PASS", claims["C1"]
    assert claims["C2"]["status"] == "PASS", claims["C2"]
    assert claims["C3"]["status"] == "HOLD_RETRACTED", claims["C3"]
    assert claims["C4"]["status"] == "HOLD_INSUFFICIENT_INDEPENDENCE", claims["C4"]

    # No same-engine duplication may satisfy an independence gate.
    single_engine = {
        "records": [
            {
                "engine": "scite",
                "ids": {"doi": "10.1234/example"},
                "title": "Example",
                "year": 2026,
                "editorial_status": ["clear"],
            },
            {
                "engine": "scite",
                "ids": {"doi": "https://doi.org/10.1234/EXAMPLE"},
                "title": "Example",
                "year": 2026,
                "editorial_status": ["clear"],
            },
        ],
        "evidence": [
            {
                "ref": "e1",
                "engine": "scite",
                "subject_alias": "doi:10.1234/example",
                "kind": "fulltext",
                "content_sha256": "0" * 64,
            }
        ],
        "claims": [
            {
                "id": "X",
                "subject_alias": "doi:10.1234/example",
                "evidence_refs": ["e1"],
                "min_independent_engines": 2,
            }
        ],
    }
    assert router.evaluate_claims(single_engine)[0]["status"] == "HOLD_INSUFFICIENT_INDEPENDENCE"

    # Zero-spend policy is executable, not prose.
    for blocked in router.PAID_OR_METERED_ACTIONS:
        assert not router.is_route_allowed(blocked)
    assert router.is_route_allowed("sider.search_open_access_works")
    assert router.is_route_allowed("scite.search_literature")

    # Domain routing adds Amass but does not replace the general scholarly layers.
    default_route = router.route_for({"domain": "general"})
    biomed_route = router.route_for({"domain": "biomed"})
    assert "amass" not in default_route
    assert biomed_route[:-1] == default_route
    assert biomed_route[-1] == "amass"

    canaries = {c["engine"]: c["status"] for c in FIXTURE["engine_canaries"]}
    assert canaries["sider_openalex"] == "PASS_BOUNDED_WITH_RESOLVER_GAP"
    assert canaries["scite"] == "PASS"
    assert canaries["alphaxiv"] == "PASS"

    print("PASS scholarly router unit canary")
    print("PASS dedupe identity canary")
    print("PASS claim/evidence gate canary")
    print("PASS retraction negative control")
    print("PASS zero-spend route guard")


if __name__ == "__main__":
    run()
