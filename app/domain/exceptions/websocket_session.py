from app.domain.exceptions.base import DomainException


class WebSocketSessionNotFound(DomainException):
    def __init__(self, message: str = "Websocket session not found") -> None:
        super().__init__(message)
