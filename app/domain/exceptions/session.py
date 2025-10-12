from app.domain.exceptions.base import DomainException


class SessionNotFound(DomainException):
    def __init__(self, message: str = "Session not found") -> None:
        super().__init__(message)


class NoSessionCookie(DomainException):
    def __init__(self, message: str = "No session cookie provided") -> None:
        super().__init__(message)


class InvalidSession(DomainException):
    def __init__(self, message: str = "Invalid or expired session") -> None:
        super().__init__(message)
