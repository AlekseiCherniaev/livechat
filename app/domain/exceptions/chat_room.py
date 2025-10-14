from app.domain.exceptions.base import DomainException


class ChatRoomNotFound(DomainException):
    def __init__(self, message: str = "Chat room not found") -> None:
        super().__init__(message)


class ChatRoomAlreadyExists(DomainException):
    def __init__(self, message: str = "Chat room already exists") -> None:
        super().__init__(message)


class NoChangesDetected(DomainException):
    def __init__(self, message: str = "Nothing to change in chat room ") -> None:
        super().__init__(message)
