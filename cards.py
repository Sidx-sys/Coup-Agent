from enum import Enum
import random


class Card(Enum):
    Captain = 0
    Assassin = 1
    Duke = 2
    Ambassador = 3
    Contessa = 4

    @classmethod
    def from_string(cls, card_name: str):
        normalized_name = card_name.strip().capitalize()
        for card in cls:
            if card.name == normalized_name:
                return card
        raise ValueError(f"Invalid card name: {card_name}")


def deal_cards(num_players: int) -> (dict, list[str]):
    if num_players * 2 > 15:
        raise ValueError("Not enough cards to deal 2 to each player")

    deck = ['Duke', 'Duke', 'Duke', 'Assassin', 'Assassin', 'Assassin',
            'Captain', 'Captain', 'Captain', 'Ambassador', 'Ambassador',
            'Ambassador', 'Contessa', 'Contessa', 'Contessa']

    # Shuffle the deck
    random.shuffle(deck)

    players_hands = {}

    for idx in range(num_players):
        players_hands[idx] = [deck.pop(), deck.pop()]

    return players_hands, deck


def draw_cards(deck: list[str], num_to_draw: int) -> list[str]:
    drawn_cards = []
    while num_to_draw:
        drawn_cards.append(deck.pop())
        num_to_draw -= 1

    return drawn_cards


def put_cards_in_deck(deck: list[str], cards: list[str]) -> list[str]:
    for card in cards:
        deck.append(card)

    random.shuffle(deck)
    return deck
