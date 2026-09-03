import hashlib

from alpha6d.canonical import canonical_json_bytes, canonicalize, sha256_hex


def test_canonical_json_sorts_keys_and_uses_compact_utf8():
    value = {"z": 1, "a": "árvíz", "nested": {"b": 2, "a": 1}}
    assert canonical_json_bytes(value) == b'{"a":"\xc3\xa1rv\xc3\xadz","nested":{"a":1,"b":2},"z":1}'


def test_canonicalize_sorts_set_like_values_lexicographically():
    value = {"items": {"beta", "alpha", "gamma"}}
    assert canonicalize(value) == {"items": ["alpha", "beta", "gamma"]}


def test_sha256_hex_hashes_canonical_bytes():
    value = {"b": 2, "a": 1}
    expected = hashlib.sha256(b'{"a":1,"b":2}').hexdigest()
    assert sha256_hex(value) == expected
