# FaultGarden

FaultGarden is a zero-spend, deterministic browser simulator for learning how autonomous-agent workflows behave under crashes, duplicate dispatch, stale authority, two-host races, ledger tampering, and replay.

## Run

Serve this `faultgarden/` directory over static HTTP and open `index.html`.

## Scenarios

NORMAL_EXECUTION, DUPLICATE_DISPATCH, CRASH_AFTER_DISPATCH, CRASH_BEFORE_RESPONSE_PERSIST, STALE_HOST_RESPONSE, TWO_HOST_RACE, TAMPERED_LEDGER_EVENT, DETERMINISTIC_REPLAY.

## Architecture

`src/engine.js` owns state transitions; `src/scenarios.js` defines fixtures; `src/ledger.js` hashes the append-only event chain; `src/replay.js` rebuilds state; `src/invariants.js` evaluates bounded invariants; `src/run.js` emits scenario verdicts; `src/app.js` + `src/ui.js` render the debugger.

## Claim ceiling

`INTERACTIVE_DETERMINISTIC_RELIABILITY_SIMULATOR__EDUCATIONAL_TEST_LAB_ONLY`

FaultGarden does not certify production systems, prove distributed consensus, or establish external timestamp authority.

## AI assistance disclosure

ChatGPT was used to help design, implement, test, and document this hackathon prototype. The implementation is deterministic and runs without external AI calls.
