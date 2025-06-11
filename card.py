from enum import Enum

class CardSuit(Enum):
    HEARTS = 1
    DIAMONDS = 2
    CLUBS = 3
    SPADES = 4

class CardValue(Enum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    QUEEN = 10
    JACK = 11
    KING = 12

class Card:
    def __init__(self, value: int, suit: int, machine_id: int):
        self.value = value
        self.suit = suit
        self.sender = machine_id

    def __str__(self):
        return f"{self.value}-{self.suit}-{self.sender}"
    
    def points(self):
        if self.value == CardValue.QUEEN.value and self.suit == CardSuit.SPADES.value:
            return 10
        
        return 1
    
    def to_dict(self):
        return {
            "value": self.value,
            "suit": self.suit,
            "sender": self.sender
        }

    @staticmethod
    def from_dict(data):
        # Map integer back to Enum
        value = CardValue(data["value"]).value
        suit = CardSuit(data["suit"]).value
        sender = data["sender"]
        return Card(value, suit, sender)