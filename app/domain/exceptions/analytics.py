from app.domain.exceptions.base import DomainException


class RoomStatsNotFound(DomainException):
    def __init__(self, message: str = "Room stats not found") -> None:
        super().__init__(message)


class UserActivityNotFound(DomainException):
    def __init__(self, message: str = "User activity not found") -> None:
        super().__init__(message)
