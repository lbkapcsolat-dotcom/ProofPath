from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

PAID_OR_METERED_ACTIONS = {
    "sider.smart_open_access_search",
    "scite.place_order",
    "browser.metered_research",
    "consensus.upgrade",
}

PASSAGE_KINDS = {"passage", "fulltext", "citation_context"}
EDITORIAL_HOLD_FLAGS = {"expression_of_concern", "correction", "erratum"}


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().lower()
    v = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", v)
    return v or None


def normalize_arxiv(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().lower()
    v = re.sub(r"^arxiv:", "", v)
    v = re.sub(r"v\d+$", "", v)
    return v or None


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def record_aliases(record: dict[str, Any]) -> list[str]:
    ids = record.get("ids", {})
    aliases: list[str] = []
    doi = normalize_doi(ids.get("doi"))
    if doi:
        aliases.append(f"doi:{doi}")
    pmid = ids.get("pmid")
    if pmid:
        aliases.append(f"pmid:{str(pmid).strip()}")
    arxiv = normalize_arxiv(ids.get("arxiv"))
    if arxiv:
        aliases.append(f"arxiv:{arxiv}")
    openalex = ids.get("openalex")
    if openalex:
        aliases.append(f"openalex:{str(openalex).strip().lower()}")
    title = record.get("title")
    year = record.get("year")
    if title and year:
        aliases.append(f"titleyear:{normalize_title(title)}:{year}")
    return aliases


def dedupe_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    groups: list[dict[str, Any]] = []
    alias_to_group: dict[str, int] = {}

    for record in records:
        aliases = record_aliases(record)
        group_ids = {alias_to_group[a] for a in aliases if a in alias_to_group}
        if len(group_ids) > 1:
            raise ValueError(f"conflicting aliases resolve to multiple groups: {aliases}")

        if group_ids:
            idx = next(iter(group_ids))
        else:
            idx = len(groups)
            groups.append({"records": [], "aliases": set()})

        groups[idx]["records"].append(record)
        groups[idx]["aliases"].update(aliases)
        for alias in aliases:
            alias_to_group[alias] = idx

    normalized: list[dict[str, Any]] = []
    for group in groups:
        records_in_group = group["records"]
        engines = sorted({r["engine"] for r in records_in_group})
        editorial_flags = sorted(
            {
                flag
                for r in records_in_group
                for flag in r.get("editorial_status", [])
                if flag and flag != "clear"
            }
        )
        canonical_alias = next(
            (
                a
                for prefix in ("doi:", "pmid:", "arxiv:", "openalex:", "titleyear:")
                for a in sorted(group["aliases"])
                if a.startswith(prefix)
            ),
            sorted(group["aliases"])[0],
        )
        normalized.append(
            {
                "canonical_alias": canonical_alias,
                "aliases": sorted(group["aliases"]),
                "engines": engines,
                "editorial_flags": editorial_flags,
                "records": records_in_group,
            }
        )
    return normalized, alias_to_group


def route_for(query: dict[str, Any]) -> list[str]:
    route = [
        "acumen",
        "sider_openalex",
        "scispace",
        "scholar_gateway",
        "alphaxiv",
        "scite",
    ]
    if query.get("domain") in {"biomed", "life_sciences", "clinical"}:
        route.append("amass")
    return route


def is_route_allowed(action: str) -> bool:
    return action not in PAID_OR_METERED_ACTIONS


def evaluate_claims(payload: dict[str, Any]) -> list[dict[str, Any]]:
    groups, alias_to_group = dedupe_records(payload["records"])
    evidence_by_ref = {e["ref"]: e for e in payload.get("evidence", [])}
    results: list[dict[str, Any]] = []

    for claim in payload.get("claims", []):
        subject = claim["subject_alias"].lower()
        if subject.startswith("doi:"):
            subject = f"doi:{normalize_doi(subject[4:])}"
        elif subject.startswith("arxiv:"):
            subject = f"arxiv:{normalize_arxiv(subject[6:])}"

        if subject not in alias_to_group:
            results.append({"id": claim["id"], "status": "HOLD_SUBJECT_NOT_FOUND"})
            continue

        group = groups[alias_to_group[subject]]
        flags = set(group["editorial_flags"])
        if "retracted" in flags:
            results.append(
                {
                    "id": claim["id"],
                    "status": "HOLD_RETRACTED",
                    "canonical_alias": group["canonical_alias"],
                }
            )
            continue
        if flags & EDITORIAL_HOLD_FLAGS:
            results.append(
                {
                    "id": claim["id"],
                    "status": "HOLD_EDITORIAL_NOTICE",
                    "flags": sorted(flags & EDITORIAL_HOLD_FLAGS),
                }
            )
            continue

        min_engines = int(claim.get("min_independent_engines", 2))
        if len(group["engines"]) < min_engines:
            results.append(
                {
                    "id": claim["id"],
                    "status": "HOLD_INSUFFICIENT_INDEPENDENCE",
                    "engines": group["engines"],
                }
            )
            continue

        refs = claim.get("evidence_refs", [])
        evidence = [evidence_by_ref[r] for r in refs if r in evidence_by_ref]
        subject_aliases = set(group["aliases"])
        evidence = [e for e in evidence if e["subject_alias"].lower() in subject_aliases]
        if not evidence:
            results.append({"id": claim["id"], "status": "HOLD_NO_EVIDENCE"})
            continue
        if not any(e.get("kind") in PASSAGE_KINDS for e in evidence):
            results.append({"id": claim["id"], "status": "HOLD_NO_PASSAGE_EVIDENCE"})
            continue
        if any(not re.fullmatch(r"[0-9a-f]{64}", e.get("content_sha256", "")) for e in evidence):
            results.append({"id": claim["id"], "status": "HOLD_BAD_EVIDENCE_HASH"})
            continue

        results.append(
            {
                "id": claim["id"],
                "status": "PASS",
                "canonical_alias": group["canonical_alias"],
                "identity_engines": group["engines"],
                "evidence_engines": sorted({e["engine"] for e in evidence}),
            }
        )
    return results


def build_report(payload: dict[str, Any]) -> dict[str, Any]:
    groups, _ = dedupe_records(payload["records"])
    claims = evaluate_claims(payload)
    canaries = payload.get("engine_canaries", [])
    return {
        "schema": "proofpath.scholarly_verifier.report.v1",
        "fixture_retrieved_at": payload.get("retrieved_at"),
        "query_route_default": route_for({"domain": "general"}),
        "query_route_biomed": route_for({"domain": "biomed"}),
        "zero_spend_forbidden_actions": sorted(PAID_OR_METERED_ACTIONS),
        "canonical_group_count": len(groups),
        "groups": [
            {
                "canonical_alias": g["canonical_alias"],
                "engines": g["engines"],
                "editorial_flags": g["editorial_flags"],
            }
            for g in groups
        ],
        "engine_canaries": canaries,
        "claims": claims,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: router.py <fixture.json>", file=sys.stderr)
        return 2
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(build_report(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
