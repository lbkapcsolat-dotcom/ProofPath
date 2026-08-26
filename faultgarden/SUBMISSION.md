# FaultGarden — GIBC Track 03 submission draft

## Elevator pitch
A digital wind tunnel for autonomous agents: inject crashes, stale authority, duplicate dispatch, two-host races, and ledger tampering, then replay the event history and see which reliability invariants survive.

## What it does
FaultGarden runs eight deterministic reliability scenarios in the browser. It visualizes two hosts, epochs, fencing tokens, event chronology, an append-only SHA-256 ledger, replay hashes, and six explicit invariants. The user can run, step, replay, tamper, reset, and export a JSON receipt.

## Built with
HTML, CSS, JavaScript ES modules, Web Crypto SHA-256, DOM, localStorage, Node built-in test runner.

## Why it matters
Agent demos often show only the happy path. FaultGarden makes ambiguous dispatch, stale responses, duplicate commits, and replay correctness visible and reproducible.

## Claim ceiling
Educational deterministic reliability simulator only; not production certification.
