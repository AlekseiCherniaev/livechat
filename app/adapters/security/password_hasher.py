from passlib.context import CryptContext
from app.domain.ports.password_hasher import PasswordHasherPort


class BcryptPasswordHasher(PasswordHasherPort):
    def __init__(self) -> None:
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        return self._pwd_context.verify(password, hashed)
