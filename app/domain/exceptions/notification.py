from app.domain.exceptions.base import DomainException


class NotificationNotFound(DomainException):
    def __init__(self, message: str = "Notification not found") -> None:
        super().__init__(message)


class NotificationPermissionError(DomainException):
    def __init__(self, message: str = "User can't access notification") -> None:
        super().__init__(message)
