from app.domain.exceptions.base import DomainException


class UserNotFound(DomainException):
    def __init__(self, message: str = "User not found") -> None:
        super().__init__(message)


class UserAlreadyExists(DomainException):
    def __init__(self, message: str = "User already exists") -> None:
        super().__init__(message)


class UserInvalidCredentials(DomainException):
    def __init__(self, message: str = "Invalid username or password") -> None:
        super().__init__(message)
