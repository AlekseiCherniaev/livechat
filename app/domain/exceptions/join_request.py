from app.domain.exceptions.base import DomainException


class JoinRequestNotFound(DomainException):
    def __init__(self, message: str = "Join request not found") -> None:
        super().__init__(message)


class JoinRequestAlreadyExists(DomainException):
    def __init__(self, message: str = "Join request already exists") -> None:
        super().__init__(message)


class JoinRequestAlreadyHandled(DomainException):
    def __init__(self, message: str = "Join request already handled") -> None:
        super().__init__(message)
