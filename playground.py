import random
from typing import Optional
from dotenv import load_dotenv

from agent import Agent
from cards import deal_cards, draw_cards, put_cards_in_deck
from state import GameState, AgentAction, ProcessAction
from langchain_openai import ChatOpenAI

load_dotenv()


class PlayGround:
    def __init__(self, num_players: int):
        """class for running agent simulations"""
        self.llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.3)

        player_hands, deck = deal_cards(num_players)
        # DEBUG
        print("Deck:", deck)
        # DEBUG

        self.players = [Agent(idx=idx, llm=self.llm, card_1=player_hands[idx][0], card_2=player_hands[idx][1]) for idx
                        in range(num_players)]
        self.deck = deck
        self.num_active_players = num_players

        # Managing Game State
        self.history = []
        self.eliminated_cards = []
        self.game_state: Optional[GameState] = None

    def execute_action(self, action_object: ProcessAction):
        if action_object.player_action.action == "Income":
            self.action_income(action_object)
        if action_object.player_action.action == "Foreign Aid":
            self.action_block_foreign_aid(action_object)
        if action_object.player_action.action == "Tax":
            self.action_tax(action_object)
        if action_object.player_action.action == "Steal":
            self.action_steal(action_object)
        if action_object.player_action.action == "Assassinate":
            self.action_assassinate(action_object)
        if action_object.player_action.action == "Exchange":
            self.action_exchange(action_object)
        if action_object.player_action.action == "Coup":
            self.action_coup(action_object)
        if action_object.player_action.action == "Challenge":
            pass
        if action_object.player_action.action == "Block Foreign Aid":
            pass
        if action_object.player_action.action == "Block Assassination":
            pass
        if action_object.player_action.action == "Block Steal":
            pass

    def update_state(self, player_idx: int, player_action: AgentAction, turn_phase: str):
        """method for updating state after a player action"""
        game_state = GameState(
            player_index=player_idx,
            player_action=player_action.action,
            target_player_index=int(player_action.target) if player_action.target else None,
            turn_phase=turn_phase
        )
        self.history.append(game_state)

    def _num_active_players(self) -> int:
        res = 0
        for player in self.players:
            if player.state.num_active_cards() > 0:
                res += 1

        return res

    def play(self):
        """method for running rounds"""
        active_player_index = 0
        num_iters = 30
        while self._num_active_players() > 1 and num_iters > 0:
            self.play_round(active_player_index)
            active_player_index = (active_player_index + 1) % len(self.players)

            while self.players[active_player_index].state.num_active_cards() == 0:
                # keep checking for a valid player to play the next move
                active_player_index = (active_player_index + 1) % len(self.players)

            num_iters -= 1

        winner_index = 0
        while self.players[winner_index].state.num_active_cards() == 0:
            winner_index = (winner_index + 1) % len(self.players)

        print("-" * 10)
        print(f"The Winner is {winner_index}")

    def play_round(self, active_player_index):
        """method for running a single round, consisting of 4 turn phases"""
        # DEBUG
        print("-" * 10)
        print("Active Player: ", active_player_index)
        print(self.players[active_player_index].state)
        # DEBUG
        active_player: Agent = self.players[active_player_index]
        opponent_states = [
            f"Player {key}, Number of Cards Left: {val.state.num_active_cards()}, Number of Coins: {val.state.number_of_coins}"
            for key, val in enumerate(self.players) if key != active_player_index]
        players_list = [idx for idx, val in enumerate(self.players) if val.state.num_active_cards() > 0]
        player_action: AgentAction = active_player.make_move(players=players_list, history=self.history,
                                                             eliminated_cards=self.eliminated_cards,
                                                             opponent_states=opponent_states)
        self.update_state(player_idx=active_player_index, player_action=player_action, turn_phase="BeginTurn")
        action_obj = ProcessAction(active_player_index=active_player_index, players=players_list,
                                   player_action=player_action, opponent_states=opponent_states, history=self.history,
                                   eliminated_cards=self.eliminated_cards, turn_phase="BeginTurn")

        # todo challenges (optional)
        # todo blocks (optional)
        # todo challenge block (optional)
        self.execute_action(action_obj)

    def action_income(self, action_object: ProcessAction):
        self.players[action_object.active_player_index].state.number_of_coins += 1

    def action_foreign_aid(self, action_object: ProcessAction):
        self.players[action_object.active_player_index].state.number_of_coins += 2

    def action_tax(self, action_object: ProcessAction):
        self.players[action_object.active_player_index].state.number_of_coins += 3

    def action_steal(self, action_object: ProcessAction):
        self.players[action_object.active_player_index].state.number_of_coins += 2
        target_player_coins = self.players[action_object.player_action.target].state.number_of_coins
        self.players[action_object.player_action.target].state.number_of_coins = max(0, target_player_coins - 2)

    def action_assassinate(self, action_object: ProcessAction):
        self.players[action_object.active_player_index].state.number_of_coins -= 3
        agent_action: AgentAction = self.players[action_object.player_action.target].drop_influence(
            players=action_object.players,
            history=action_object.history,
            eliminated_cards=action_object.eliminated_cards,
            opponent_states=action_object.opponent_states
        )
        self.eliminated_cards.append(agent_action.card_to_discard)

    def action_exchange(self, action_object: ProcessAction):
        active_player_idx = action_object.active_player_index
        new_cards: list = draw_cards(self.deck, num_to_draw=2)
        num_active_cards = self.players[active_player_idx].state.num_active_cards()

        total_cards = [self.players[active_player_idx].state.card_1,
                       self.players[active_player_idx].state.card_2] + new_cards
        random.shuffle(total_cards)
        switch_cards = []
        for i in range(num_active_cards):
            switch_cards.append(total_cards.pop())

        put_cards_in_deck(self.deck, total_cards)
        self.players[active_player_idx].state.switch_cards(switch_cards)

    def action_coup(self, action_object: ProcessAction):
        self.players[action_object.active_player_index].state.number_of_coins -= 7
        agent_action: AgentAction = self.players[action_object.player_action.target].drop_influence(
            players=action_object.players,
            history=action_object.history,
            eliminated_cards=action_object.eliminated_cards,
            opponent_states=action_object.opponent_states
        )
        self.eliminated_cards.append(agent_action.card_to_discard)

    def action_challenge(self, action_object: ProcessAction):
        # todo need to implement challenge flow
        pass

    def action_block_foreign_aid(self, action_object: ProcessAction):
        # todo need to implement blocking flow
        pass

    def action_block_steal(self, action_object: ProcessAction):
        # todo need to implement blocking flow
        pass

    def action_block_assassination(self, action_object: ProcessAction):
        # todo need to implement blocking flow
        pass
