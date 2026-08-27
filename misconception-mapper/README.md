# Misconception Mapper V1

Standalone educational prototype for the Prometheus September AI Challenge 2.

Claim ceiling: A prototype educational tool that identifies bounded misconception patterns and provides Socratic hints to support retry-based learning.

Runtime constraints:
- zero paid APIs
- zero required network calls
- zero database
- local session state only
- deterministic heuristic path is authoritative for V1

Run tests:

```bash
npm test
```

The Misconception Mapper core does not import the existing ProofPath runtime.
