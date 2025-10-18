from app.domain.exceptions.base import DomainException


class RoomNotFound(DomainException):
    def __init__(self, message: str = "Room not found") -> None:
        super().__init__(message)


class RoomAlreadyExists(DomainException):
    def __init__(self, message: str = "Room already exists") -> None:
        super().__init__(message)


class NoChangesDetected(DomainException):
    def __init__(self, message: str = "Nothing to change in room") -> None:
        super().__init__(message)


class RoomPermissionError(DomainException):
    def __init__(self, message: str = "User can't access room") -> None:
        super().__init__(message)
