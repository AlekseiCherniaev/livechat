from app.domain.exceptions.base import DomainException


class NoSessionCookie(DomainException):
    def __init__(self, message: str = "No session cookie provided") -> None:
        super().__init__(message)


class InvalidSession(DomainException):
    def __init__(self, message: str = "Invalid or expired session") -> None:
        super().__init__(message)
