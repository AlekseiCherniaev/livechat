from enum import Enum


class Environment(Enum):
    TEST = "TEST"
    DEV = "DEV"
    PROD = "PROD"


class EventType(Enum):
    MESSAGE_SENT = "MESSAGE_SENT"
    USER_JOINED = "USER_JOINED"
    USER_LEFT = "USER_LEFT"
