from app.domain.exceptions.base import DomainException


class MessageNotFound(DomainException):
    def __init__(self, message: str = "Message not found") -> None:
        super().__init__(message)


class MessagePermissionError(DomainException):
    def __init__(self, message: str = "Cannot access another user's message") -> None:
        super().__init__(message)
