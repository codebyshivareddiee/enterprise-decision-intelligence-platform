import bcrypt

# Monkeypatch to fix passlib + bcrypt compatibility issue on newer bcrypt/python versions
if not hasattr(bcrypt, "__about__"):
    class About:
        __version__ = bcrypt.__version__
    bcrypt.__about__ = About()

# Wrap bcrypt.hashpw to truncate passwords to 72 bytes to avoid ValueError on bcrypt >= 4.1.0/5.0.0
# which passlib triggers during backend detection testing.
original_hashpw = bcrypt.hashpw
def patched_hashpw(password, salt):
    if isinstance(password, bytes) and len(password) > 72:
        password = password[:72]
    elif isinstance(password, str) and len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72]
    return original_hashpw(password, salt)
bcrypt.hashpw = patched_hashpw

from passlib.context import CryptContext

# Configure passlib to use bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password[:72])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash."""
    return pwd_context.verify(plain_password[:72], hashed_password)
