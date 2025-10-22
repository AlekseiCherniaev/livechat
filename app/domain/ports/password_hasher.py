from typing import Protocol


class PasswordHasherPort(Protocol):
    def hash(self, password: str) -> str:
        pass

    def verify(self, password: str, hashed: str) -> bool:
        pass
