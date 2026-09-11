#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Mapping
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3

import alpha_full_6d_local_control_plane_v6_1 as core

SCHEMA = "HV_V6_1_RUNTIME_ENFORCEMENT_V1"
DURABLE_SCHEMA_VERSION = 1
PASS_VERDICT = "PASS_HV_V6_1_RUNTIME_ENFORCEMENT"


class ClaimLevel(IntEnum):
    SUPPORT = 0
    LOCAL_TEST = 1
    RUNTIME = 2
    PRODUCTION = 3
    GLOBAL = 4


class DurableStateError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeRequest:
    candidate_id: str
    evidence_state: str
    authority_context: Mapping[str, Any] | None
    claim_level: ClaimLevel
    requires_recovery: bool = False
    support_only: bool = False


@dataclass(frozen=True)
class RuntimeDecision:
    verdict: str
    executable: bool
    obligation: str
    reason: str
    k_state: str
    core_verdict: str = ""


@dataclass
class HVRuntimeLedger:
    claim_ceiling: ClaimLevel
    consumed_nonces: set[str] = field(default_factory=set)
    revoked_provider_statement_hashes: dict[str, int] = field(default_factory=dict)
    candidates: list[str] = field(default_factory=list)
    revocation_epoch: int = 0
    _db: sqlite3.Connection | None = field(default=None, repr=False, compare=False)
    _db_path: str | None = field(default=None, repr=False, compare=False)

    @classmethod
    def open_durable(cls, path: str | os.PathLike[str], claim_ceiling: ClaimLevel) -> "HVRuntimeLedger":
        ledger = cls(claim_ceiling=claim_ceiling)
        ledger._open_durable(path)
        return ledger

    def _open_durable(self, path: str | os.PathLike[str]) -> None:
        db_path = Path(path)
        if not db_path.parent.exists():
            raise DurableStateError("DURABLE_STATE_PARENT_MISSING")
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0, isolation_level=None)
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("PRAGMA foreign_keys=ON")

            meta_exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta'"
            ).fetchone() is not None
            if meta_exists:
                row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
                if row is not None and row[0] != str(DURABLE_SCHEMA_VERSION):
                    raise DurableStateError(
                        f"DURABLE_STATE_SCHEMA_VERSION_MISMATCH:{row[0]}!={DURABLE_SCHEMA_VERSION}"
                    )

            conn.execute("BEGIN IMMEDIATE")
            conn.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute(
                "INSERT OR IGNORE INTO meta(key,value) VALUES('schema_version',?)",
                (str(DURABLE_SCHEMA_VERSION),),
            )
            conn.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('revocation_epoch','0')")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS consumed_nonces("
                "nonce TEXT PRIMARY KEY, consumed_at TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS revocations("
                "provider_hash TEXT PRIMARY KEY, epoch INTEGER NOT NULL CHECK(epoch > 0))"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS candidates("
                "candidate_id TEXT PRIMARY KEY, first_seen TEXT NOT NULL)"
            )
            conn.execute("COMMIT")

            integrity = conn.execute("PRAGMA integrity_check").fetchone()
            if integrity is None or integrity[0] != "ok":
                raise DurableStateError("DURABLE_STATE_INTEGRITY_CHECK_FAILED")

            epoch_row = conn.execute("SELECT value FROM meta WHERE key='revocation_epoch'").fetchone()
            self.revocation_epoch = int(epoch_row[0]) if epoch_row else 0
            self._db = conn
            self._db_path = str(db_path)
            try:
                os.chmod(db_path, 0o600)
            except OSError:
                pass
        except DurableStateError:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
            raise
        except (sqlite3.Error, OSError, ValueError) as e:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
            raise DurableStateError(f"DURABLE_STATE_UNAVAILABLE:{type(e).__name__}:{e}") from e

    @property
    def durable(self) -> bool:
        return self._db is not None

    def _require_db(self) -> sqlite3.Connection:
        if self._db is None:
            raise DurableStateError("DURABLE_STATE_NOT_OPEN")
        return self._db

    def close(self) -> None:
        if self._db is not None:
            self._db.close()
            self._db = None

    def record_candidate(self, candidate_id: str) -> None:
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("CANDIDATE_ID_REQUIRED")
        if candidate_id not in self.candidates:
            self.candidates.append(candidate_id)
        if self._db is not None:
            try:
                self._db.execute(
                    "INSERT OR IGNORE INTO candidates(candidate_id, first_seen) VALUES(?,?)",
                    (candidate_id, datetime.now(timezone.utc).isoformat()),
                )
            except sqlite3.Error as e:
                raise DurableStateError(f"DURABLE_STATE_CANDIDATE_WRITE_FAILED:{e}") from e

    def revoke(self, authority_context: Mapping[str, Any]) -> int:
        provider = authority_context.get("provider_statement")
        digest = core.signed_record_sha256(provider)
        if self._db is None:
            self.revocation_epoch += 1
            self.revoked_provider_statement_hashes[digest] = self.revocation_epoch
            return self.revocation_epoch

        db = self._require_db()
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT value FROM meta WHERE key='revocation_epoch'").fetchone()
            current = int(row[0]) if row else 0
            epoch = current + 1
            db.execute("UPDATE meta SET value=? WHERE key='revocation_epoch'", (str(epoch),))
            db.execute(
                "INSERT INTO revocations(provider_hash,epoch) VALUES(?,?) "
                "ON CONFLICT(provider_hash) DO UPDATE SET epoch=excluded.epoch",
                (digest, epoch),
            )
            db.execute("COMMIT")
        except sqlite3.Error as e:
            try:
                db.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise DurableStateError(f"DURABLE_STATE_REVOCATION_WRITE_FAILED:{e}") from e
        self.revocation_epoch = epoch
        self.revoked_provider_statement_hashes[digest] = epoch
        return epoch

    def is_revoked(self, provider_hash: str) -> bool:
        if self._db is None:
            return provider_hash in self.revoked_provider_statement_hashes
        try:
            return self._db.execute(
                "SELECT 1 FROM revocations WHERE provider_hash=?",
                (provider_hash,),
            ).fetchone() is not None
        except sqlite3.Error as e:
            raise DurableStateError(f"DURABLE_STATE_REVOCATION_READ_FAILED:{e}") from e

    def consume_nonce_once(self, nonce: str) -> bool:
        if not isinstance(nonce, str) or not nonce:
            raise ValueError("NONCE_REQUIRED")
        if self._db is None:
            if nonce in self.consumed_nonces:
                return False
            self.consumed_nonces.add(nonce)
            return True

        db = self._require_db()
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT INTO consumed_nonces(nonce,consumed_at) VALUES(?,?)",
                (nonce, datetime.now(timezone.utc).isoformat()),
            )
            db.execute("COMMIT")
            self.consumed_nonces.add(nonce)
            return True
        except sqlite3.IntegrityError:
            try:
                db.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            return False
        except sqlite3.Error as e:
            try:
                db.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise DurableStateError(f"DURABLE_STATE_NONCE_WRITE_FAILED:{e}") from e

    def durable_snapshot(self) -> dict[str, Any]:
        db = self._require_db()
        try:
            integrity_row = db.execute("PRAGMA integrity_check").fetchone()
            version_row = db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
            epoch_row = db.execute("SELECT value FROM meta WHERE key='revocation_epoch'").fetchone()
            return {
                "schema": "HV_V6_1_DURABLE_RUNTIME_LEDGER_V1",
                "schema_version": int(version_row[0]) if version_row else -1,
                "integrity_check": integrity_row[0] if integrity_row else "missing",
                "journal_mode": db.execute("PRAGMA journal_mode").fetchone()[0],
                "synchronous": int(db.execute("PRAGMA synchronous").fetchone()[0]),
                "consumed_nonce_count": int(db.execute("SELECT COUNT(*) FROM consumed_nonces").fetchone()[0]),
                "revocation_count": int(db.execute("SELECT COUNT(*) FROM revocations").fetchone()[0]),
                "candidate_count": int(db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]),
                "revocation_epoch": int(epoch_row[0]) if epoch_row else 0,
            }
        except sqlite3.Error as e:
            raise DurableStateError(f"DURABLE_STATE_SNAPSHOT_FAILED:{e}") from e


OBLIGATION_TO_HOOK = {
    "OBL-01": "resolve_hv_runtime: missing authority branch",
    "OBL-02": "resolve_hv_runtime: core.resolve_gate exact V validation",
    "OBL-03": "resolve_hv_runtime: current_edge_sha256 == context.input_sha256",
    "OBL-04": "resolve_hv_runtime: current_state_sha256 == context.raw_export_sha256",
    "OBL-05": "resolve_hv_runtime: current_policy_sha256 == context.policy_sha256",
    "OBL-06": "HVRuntimeLedger.consume_nonce_once atomic single-use check",
    "OBL-07": "resolve_hv_runtime: provider freshness check plus core freshness revalidation",
    "OBL-08": "HVRuntimeLedger durable revoked provider-statement registry",
    "OBL-09": "HVRuntimeLedger.claim_ceiling non-escalation check",
    "OBL-10": "k_from_evidence total tri-state UNKNOWN->HOLD mapping",
    "OBL-11": "HVRuntimeLedger.record_candidate before authority decision",
    "OBL-12": "resolve_hv_runtime: recovery authority external-required branch",
    "OBL-13": "resolve_hv_runtime: K=HOLD non-executable branch",
    "OBL-14": "resolve_hv_runtime: K=DENY non-executable branch",
    "OBL-15": "resolve_hv_runtime: K=PASS with absent V non-executable branch",
    "OBL-16": "resolve_hv_runtime: final PASS only after all guards plus core PASS",
    "OBL-17": "attempt_horizontal_mint_v unconditional rejection",
    "OBL-18": "support_only branch plus support_mutations all false",
}


def support_mutations() -> dict[str, bool]:
    return {
        "pointer": False,  # OBL-18
        "global": False,
        "runtime": False,
        "production": False,
    }


def k_from_evidence(evidence_state: str) -> str:
    mapping = {
        "UNKNOWN": "HOLD",
        "PROVEN_NEGATIVE": "DENY",
        "PROVEN_SUFFICIENT": "PASS",
    }
    return mapping.get(evidence_state, "HOLD")


def attempt_horizontal_mint_v(_horizontal_material: Mapping[str, Any]) -> bool:
    raise PermissionError("H_ONLY_CANNOT_MINT_V")


def _hold(obligation: str, verdict: str, reason: str, *, k_state: str = "HOLD", core_verdict: str = "") -> RuntimeDecision:
    return RuntimeDecision(
        verdict=verdict,
        executable=False,
        obligation=obligation,
        reason=reason,
        k_state=k_state,
        core_verdict=core_verdict,
    )


def _pass(obligation: str, reason: str, *, k_state: str = "PASS") -> RuntimeDecision:
    return RuntimeDecision(
        verdict=PASS_VERDICT,
        executable=True,
        obligation=obligation,
        reason=reason,
        k_state=k_state,
        core_verdict=core.PASS_VERDICT,
    )


def _provider_fresh(authority_context: Mapping[str, Any], now: datetime) -> bool:
    try:
        provider = authority_context["provider_statement"]
        body = provider["body"]
        return core._freshness(body, now) == "FRESH"
    except Exception:
        return False


def _provider_statement_hash(authority_context: Mapping[str, Any]) -> str:
    return core.signed_record_sha256(authority_context["provider_statement"])


def resolve_hv_runtime(
    request: RuntimeRequest,
    ledger: HVRuntimeLedger,
    *,
    now: datetime | None = None,
    current_edge_sha256: str,
    current_state_sha256: str,
    current_policy_sha256: str,
) -> RuntimeDecision:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        return _hold("OBL-07", "HOLD_TIMEZONE_REQUIRED", "RUNTIME_TIME_MUST_BE_AWARE")

    ledger.record_candidate(request.candidate_id)
    k_state = k_from_evidence(request.evidence_state)

    if request.support_only:
        return _hold("OBL-18", "HOLD_SUPPORT_ONLY_NONACTUATING", "SUPPORT_PATH_CANNOT_ACTUATE", k_state=k_state)

    if request.authority_context is None:
        if k_state == "PASS":
            return _hold("OBL-15", "HOLD_PASS_WITHOUT_V", "K_PASS_REQUIRES_VERTICAL_AUTHORITY", k_state=k_state)
        return _hold("OBL-01", "HOLD_MISSING_V", "MISSING_VERTICAL_AUTHORITY")

    if k_state == "HOLD":
        return _hold("OBL-13", "HOLD_K_STATE", "K_HOLD_NONEXECUTABLE", k_state=k_state)
    if k_state == "DENY":
        return _hold("OBL-14", "DENY_K_STATE", "K_DENY_NONEXECUTABLE", k_state=k_state)

    context = request.authority_context
    if current_edge_sha256 != context.get("input_sha256"):
        return _hold("OBL-03", "HOLD_EDGE_BIND_MISMATCH", "EDGE_CHANGED_AFTER_APPROVAL")
    if current_state_sha256 != context.get("raw_export_sha256"):
        return _hold("OBL-04", "HOLD_STATE_BIND_MISMATCH", "STATE_CHANGED_AFTER_APPROVAL")
    if current_policy_sha256 != context.get("policy_sha256"):
        return _hold("OBL-05", "HOLD_POLICY_BIND_MISMATCH", "POLICY_CHANGED_AFTER_APPROVAL")

    if not _provider_fresh(context, now):
        return _hold("OBL-07", "HOLD_EXPIRED_V", "AUTHORITY_NOT_FRESH")

    provider_hash = _provider_statement_hash(context)
    if ledger.is_revoked(provider_hash):
        return _hold("OBL-08", "HOLD_REVOKED_V", "NEWER_REVOCATION_DOMINATES")

    if request.claim_level > ledger.claim_ceiling:
        return _hold("OBL-09", "HOLD_CLAIM_ABOVE_CEILING", "CLAIM_ESCALATION_BLOCKED")

    if request.requires_recovery:
        return _hold("OBL-12", "HOLD_RECOVERY_AUTHORITY_EXTERNAL_REQUIRED", "RUNTIME_CANNOT_DERIVE_RECOVERY_AUTHORITY")

    core_decision = core.resolve_gate(context, now=now)
    if core_decision.verdict != core.PASS_VERDICT:
        return _hold("OBL-02", "HOLD_INVALID_V", core_decision.verdict)

    nonce = context.get("nonce")
    if not isinstance(nonce, str) or not nonce:
        return _hold("OBL-02", "HOLD_INVALID_V", "NONCE_REQUIRED")
    if not ledger.consume_nonce_once(nonce):
        return _hold("OBL-06", "HOLD_REPLAYED_V", "NONCE_ALREADY_CONSUMED")

    return _pass("OBL-16", "ALL_RUNTIME_GUARDS_SATISFIED", k_state=k_state)


if __name__ == "__main__":
    import json
    print(json.dumps({
        "schema": SCHEMA,
        "durable_schema_version": DURABLE_SCHEMA_VERSION,
        "obligations_mapped": len(OBLIGATION_TO_HOOK),
        "original_core_alone_enforces_all_18": False,
        "support_mutations": support_mutations(),
    }, sort_keys=True))
