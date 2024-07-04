from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Literal, Optional, Union, List


class PlayerState(BaseModel):
    number_of_coins: int = Field(2, ge=0, le=12)
    card_1: Literal['Duke', 'Assassin', 'Ambassador', 'Captain', 'Contessa'] = Field(...)
    card_2: Literal['Duke', 'Assassin', 'Ambassador', 'Captain', 'Contessa'] = Field(...)
    card_1_alive: bool = Field(True)
    card_2_alive: bool = Field(True)

    def discard_card(self, card_name: str):
        if card_name == self.card_1:
            self.card_1_alive = False
        elif card_name == self.card_2:
            self.card_2_alive = False
        else:
            raise ValueError(f"Invalid card name {card_name}. Choose {self.card_1} or {self.card_2}")

    def num_active_cards(self) -> int:
        res = 0
        if self.card_1_alive:
            res += 1
        if self.card_2_alive:
            res += 1

        return res

    def switch_cards(self, cards: list[str]):
        if len(cards) == 1:
            if self.card_1_alive:
                self.card_1 = cards[0]
            elif self.card_2_alive:
                self.card_2 = cards[0]
        else:
            self.card_1 = cards[0]
            self.card_2 = cards[1]

    def active_cards(self) -> list[str]:
        res = []
        if self.card_1_alive:
            res.append(self.card_1)
        if self.card_2_alive:
            res.append(self.card_2)
        return res

    def switch_with_new(self, card_to_discard: str, deck: list[str]):
        new_card = deck.pop()
        if self.card_1 == card_to_discard:
            self.card_1 = new_card
        else:
            self.card_2 = new_card


class TurnPhase(Enum):
    BeginTurn = 0
    ChallengeAction = 1
    BlockAction = 2
    ChallengeBlock = 3


class GameState(BaseModel):
    player_index: int = Field(..., ge=0, le=7)
    player_action: Literal[
        'Income', 'Foreign Aid', 'Coup', 'Tax', 'Assassinate', 'Exchange', 'Steal', 'Challenge', 'Block Foreign Aid', 'Block Steal', 'Block Assassination'] = Field(
        ...)
    target_player_index: Optional[Union[None, int]] = Field(..., ge=0, le=7)


class AgentAction(BaseModel):
    action: Optional[Literal['Income', 'Foreign Aid', 'Coup', 'Tax', 'Assassinate', 'Exchange', 'Steal', 'Challenge', 'Block Foreign Aid', 'Block Steal', 'Block Assassination', 'None']] = Field(None)
    target: Optional[Union[None, int]] = None
    card_to_discard: Optional[Literal['Duke', 'Assassin', 'Ambassador', 'Captain', 'Contessa']] = None
    counter_action: Optional[Literal['Challenge', 'Block Foreign Aid', 'Block Steal', 'Block Assassination', 'None']] = Field(None)
    intuition: str

    @field_validator('target', mode='before')
    def str_to_int(cls, v):
        if isinstance(v, str):
            return int(v)
        return v


class ProcessAction(BaseModel):
    active_player_index: int
    players: Optional[List[int]]
    history: Optional[List[GameState]]
    eliminated_cards: Optional[List[str]]
    opponent_states: Optional[list[str]]
    player_action: AgentAction
