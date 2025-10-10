from app.domain.exceptions.base import DomainException


class SessionNotFound(DomainException):
    def __init__(self, message: str = "Session not found") -> None:
        super().__init__(message)
