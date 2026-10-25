"""Password hashing helpers backed by Argon2id."""
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
_hasher = PasswordHasher()
def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Passwords must be at least 12 characters long")
    return _hasher.hash(password)
def verify_password(password: str, hashed: str) -> bool:
    try: return _hasher.verify(hashed, password)
    except (VerifyMismatchError, InvalidHashError, TypeError): return False
