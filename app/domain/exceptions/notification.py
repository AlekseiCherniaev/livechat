from app.domain.exceptions.base import DomainException


class NotificationNotFound(DomainException):
    def __init__(self, message: str = "Notification not found") -> None:
        super().__init__(message)
