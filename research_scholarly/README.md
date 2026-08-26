# ProofPath Scholarly Multi-Engine Verifier

This directory implements the fail-closed scholarly research gate used by ProofPath.

## Goal

The verifier does **not** treat a search result as scientific authority. It separates:

1. freshness preflight,
2. broad discovery,
3. semantic discovery,
4. peer-reviewed passage evidence,
5. preprint/full-text inspection,
6. citation/editorial checks,
7. domain primary-source resolution,
8. deterministic identity deduplication,
9. claim-to-evidence admission.

## Engine roles

- `acumen`: currentness / omission preflight.
- `sider_openalex`: high-recall discovery and OpenAlex metadata.
- `scispace`: semantic discovery.
- `scholar_gateway`: peer-reviewed passage evidence and provenance.
- `alphaxiv`: arXiv/preprint PDF pages and linked code repositories.
- `scite`: full-text snippets, citation context, retractions/corrections/concerns.
- `amass`: life-science domain authority (PubMed/PMC, trials, drugs, genes, regulatory records).

No single engine can grant a research claim `PASS` by itself.

## Admission rules

A normal positive claim receives `PASS` only when all of the following hold:

- the subject resolves to a canonical identity (DOI, PMID, arXiv, OpenAlex, or bounded title/year fallback),
- at least two distinct engine identities corroborate the subject unless a stricter claim rule is supplied,
- at least one hash-bound passage/full-text/citation-context evidence item is attached,
- no retraction is present,
- no unresolved expression of concern, correction, or erratum is present.

Fail-closed outcomes include:

- `HOLD_SUBJECT_NOT_FOUND`
- `HOLD_INSUFFICIENT_INDEPENDENCE`
- `HOLD_NO_EVIDENCE`
- `HOLD_NO_PASSAGE_EVIDENCE`
- `HOLD_BAD_EVIDENCE_HASH`
- `HOLD_EDITORIAL_NOTICE`
- `HOLD_RETRACTED`

Retraction wins over all positive evidence.

## Canary evidence

`fixtures/canary_records.json` freezes live connector observations from 2026-08-26. It intentionally includes:

- one peer-reviewed paper resolved independently by SciSpace, Scholar Gateway, and Scite;
- one 2026 arXiv paper resolved by Sider/OpenAlex and alphaXiv, with page-level PDF evidence;
- one known retracted paper as a mandatory negative control;
- one Amass biomedical record that remains `HOLD_INSUFFICIENT_INDEPENDENCE` until another independent engine corroborates it;
- a Sider DOI-resolver failure, recorded as `PASS_BOUNDED_WITH_RESOLVER_GAP` rather than hidden.

The fixture stores identifiers, locators and content hashes rather than long copyrighted passages.

## Zero-spend policy

The executable route guard blocks known paid or metered paths:

- `sider.smart_open_access_search`
- `scite.place_order`
- `browser.metered_research`
- `consensus.upgrade`

Free/read-only discovery and verification routes remain allowed.

## Verification

Run locally:

```bash
python3 research_scholarly/test_router.py
python3 research_scholarly/router.py research_scholarly/fixtures/canary_records.json
```

The GitHub workflow runs the same deterministic checks and emits SHA-256 hashes for the fixture and generated report.

## Claim ceiling

A green canary proves the router's identity, dedupe, evidence, editorial, and zero-spend invariants against the frozen evidence set. It does **not** prove literature completeness for every future query. Live research still has to execute the multi-engine retrieval lane, preserve provenance, and refresh the fixture when engine behavior or source state materially changes.
