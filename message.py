from enum import Enum

class RingMessageType(Enum):
    CONNECT = 1
    SETUP = 2
    TOKEN = 3
    POINTS = 4
    END = 5
    TURN_OFF = 6


class RingMessage:

    def __init__(self, type: RingMessageType, content: str, target: int):
        self.type = type.value
        self.payload = content
        self.target = target

    def __str__(self):
        return f"{self.type};{self.target};{self.payload}"
    
    def to_bytes(self):
        return self.__str__().encode("utf-8")