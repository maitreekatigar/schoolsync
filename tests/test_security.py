from app.security import hash_password, verify_password
import pytest

def test_password_hash_roundtrip():
    raw = "correct horse battery staple 2026"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed)
    assert not verify_password("not the password", hashed)

def test_password_minimum_length():
    with pytest.raises(ValueError):
        hash_password("short")
