from typing_extensions import Protocol


class PasswordHasherPort(Protocol):
    @staticmethod
    def hash(password: str) -> str:
        pass

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        pass
