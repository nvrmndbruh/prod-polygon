import time
import pytest
from datetime import timedelta

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)


class TestPasswordHashing:
    def test_hash_and_verify_correct(self):
        password = "secureP@ss1"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        password = "secureP@ss1"
        hashed = get_password_hash(password)
        assert verify_password("wrong_password", hashed) is False

    def test_verify_empty_password(self):
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True
        assert verify_password(" ", hashed) is False

    def test_verify_with_broken_hash(self):
        assert verify_password("anything", "not_a_hash") is False


class TestJWT:
    def test_create_and_decode_valid_token(self):
        data = {"sub": "user123"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert "exp" in decoded

    def test_decode_invalid_token(self):
        decoded = decode_access_token("invalid.token.string")
        assert decoded is None

    def test_token_expiration(self):
        token = create_access_token({"sub": "test"}, expires_delta=timedelta(seconds=-1))
        decoded = decode_access_token(token)
        assert decoded is None

    def test_token_with_different_algorithm(self):
        token = create_access_token({"sub": "test"})
        parts = token.split('.')
        tampered = parts[0] + '.tampered.' + parts[2]
        decoded = decode_access_token(tampered)
        assert decoded is None