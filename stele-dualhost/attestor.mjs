import crypto from 'node:crypto';

export function canonicalJson(value) {
  if (value === null) return 'null';
  if (typeof value === 'string') return JSON.stringify(value);
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new Error('non-finite number');
    return JSON.stringify(value);
  }
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (Array.isArray(value)) return '[' + value.map(canonicalJson).join(',') + ']';
  if (typeof value === 'object') {
    return '{' + Object.keys(value).sort().map(k => JSON.stringify(k)+':'+canonicalJson(value[k])).join(',') + '}';
  }
  throw new Error(`unsupported canonical JSON type: ${typeof value}`);
}

function sha256Hex(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

export function createSignedAttestation({host_id, host_role, shared_claims, host_evidence}) {
  if (!host_id || typeof host_id !== 'string') throw new Error('host_id required');
  if (!host_role || typeof host_role !== 'string') throw new Error('host_role required');
  if (!shared_claims || typeof shared_claims !== 'object') throw new Error('shared_claims required');
  if (!host_evidence || typeof host_evidence !== 'object') throw new Error('host_evidence required');
  const payload = {schema:'STELE_DUAL_HOST_SIGNED_ATTESTATION_V1',host_id,host_role,shared_claims,host_evidence};
  const canonical = canonicalJson(payload);
  const {publicKey, privateKey} = crypto.generateKeyPairSync('ed25519');
  const signature = crypto.sign(null, Buffer.from(canonical), privateKey);
  const publicKeyPem = publicKey.export({type:'spki',format:'pem'}).toString();
  const publicKeyDer = publicKey.export({type:'spki',format:'der'});
  return {
    schema:'STELE_SIGNED_ATTESTATION_ENVELOPE_V1',
    signature_algorithm:'Ed25519',
    canonicalization:'RECURSIVE_UTF8_JSON_SORTED_KEYS_V1',
    payload_sha256:sha256Hex(Buffer.from(canonical)),
    public_key_fingerprint_sha256:sha256Hex(publicKeyDer),
    public_key_pem:publicKeyPem,
    signature_base64:signature.toString('base64'),
    payload,
  };
}
