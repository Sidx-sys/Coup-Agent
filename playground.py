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
        self.action_player_map: dict = {
            "Income": ['Duke', 'Assassin', 'Ambassador', 'Captain', 'Contessa'],
            "Steal": ['Captain'],
            "Exchange": ['Ambassador'],
            "Tax": ["Duke"],
            "Assassinate": ["Assassin"],
            "Block Steal": ['Ambassador', 'Captain'],
            "Block Assassination": ["Contessa"],
            "Block Foreign Aid": ["Duke"]
        }

    def execute_action(self, action_object: ProcessAction):
        if action_object.player_action.action == "Income":
            self.action_income(action_object)
        if action_object.player_action.action == "Foreign Aid":
            self.action_foreign_aid(action_object)
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

    def update_state(self, player_idx: int, player_action: AgentAction):
        """method for updating state after a player action"""
        game_state = GameState(
            player_index=player_idx,
            player_action=player_action.action,
            target_player_index=int(player_action.target) if player_action.target else None,
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

        self.update_state(player_idx=active_player_index, player_action=player_action)
        action_object = ProcessAction(
            active_player_index=active_player_index,
            players=players_list,
            player_action=player_action,
            opponent_states=opponent_states,
            history=self.history,
            eliminated_cards=self.eliminated_cards,
        )

        print("***Checking For Challenge Action or Block Action***")
        counter_action: dict = self.action_block_or_challenge(action_object=action_object)

        if counter_action["challenge_success"]:
            return

        print("***Checking For Challenge on Block Action***")
        if counter_action["block_success"]:
            block_action_object = ProcessAction(
                active_player_index=active_player_index,
                players=players_list,
                player_action=AgentAction(action=counter_action["counter_action"], target=player_action.target,
                                          intuition="Challenging Block"),
                opponent_states=opponent_states,
                history=self.history,
                eliminated_cards=self.eliminated_cards,
            )
            challenge_block = self.action_challenge_block(block_action_object)

            if not challenge_block["challenge_success"]:
                # agent was not successful in challenging the block, meaning the action fails
                return

        self.execute_action(action_object)

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
        agent_action: AgentAction = self.players[action_object.player_action.target].drop_influence(action_object)
        if agent_action.card_to_discard is None:
            return
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
        agent_action: AgentAction = self.players[action_object.player_action.target].drop_influence(action_object)
        if agent_action.card_to_discard is None:
            # todo make sure the agent is not eliminated cards with no option, can be a prompt level change too
            return
        self.eliminated_cards.append(agent_action.card_to_discard)

    def action_challenge(self, action_object: ProcessAction) -> dict:
        # pick a random order (range(0, 4)) for income, tax, foreign aid and exchange
        # otherwise only the targeted player for assassination and steal
        order: list[int] = random.sample(range(len(self.players)), k=len(self.players))

        agent_response: Optional[AgentAction] = None
        challenger_index = None
        if action_object.player_action.action in ["Assassinate", "Steal"]:
            agent_response: AgentAction = self.players[action_object.player_action.target].do_challenge(
                action_object=action_object)
            challenger_index = action_object.player_action.target
        else:
            for player_index in order:
                if player_index == action_object.active_player_index or self.players[player_index].state.num_active_cards() == 0:
                    continue
                agent_response: AgentAction = self.players[player_index].do_challenge(action_object=action_object)
                if agent_response.challenge:
                    challenger_index = player_index
                    break

        if not agent_response:
            return {"challenge_success": False}

        to_challenge: bool = True if agent_response.counter_action == "Challenge" else False

        if not to_challenge:
            return {"challenge_success": False}

        action_used: str = action_object.player_action.action
        player_active_cards: set[str] = set(self.players[action_object.active_player_index].state.active_cards())
        allowed_cards: set[str] = set(self.action_player_map[action_used])
        is_valid_move: bool = not allowed_cards.isdisjoint(player_active_cards)
        chosen_cards: list[str] = list(allowed_cards.intersection(player_active_cards))

        if is_valid_move:
            self.players[challenger_index].drop_influence(action_object)
            self.players[action_object.active_player_index].state.switch_with_new(card_to_discard=chosen_cards[-1],
                                                                                  deck=self.deck)
            self.eliminated_cards.append(chosen_cards[-1])
            return {"challenge_success": False}

        agent_action: AgentAction = self.players[action_object.active_player_index].drop_influence(action_object)
        self.eliminated_cards.append(agent_action.card_to_discard)

        return {"challenge_success": True}

    def action_block_or_challenge(self, action_object: ProcessAction) -> dict[str, bool]:
        order: list[int] = random.sample(range(len(self.players)), k=len(self.players))

        opposition_index = None
        agent_response: Optional[AgentAction] = None

        if action_object.player_action.action in ["Assassinate", "Steal", "Foreign Aid"]:
            agent_response: AgentAction = self.players[action_object.player_action.target].do_block_or_challenge(
                action_object=action_object)
            opposition_index = action_object.player_action.target
        else:
            for player_index in order:
                if player_index == action_object.active_player_index or self.players[player_index].state.num_active_cards() == 0:
                    continue
                agent_response: AgentAction = self.players[player_index].do_challenge(action_object=action_object)
                if agent_response.counter_action == "Challenge":
                    opposition_index = player_index
                    break

        if not agent_response:
            return {"challenge_success": False, "block_success": False, "counter_action": "None",
                    "opposition_index": None}

        to_challenge: bool = True if agent_response.counter_action == "Challenge" else False
        to_block: bool = True if agent_response.counter_action in ['Block Foreign Aid', 'Block Steal',
                                                                   'Block Assassinate'] else False

        if not to_challenge and not to_block:
            return {"challenge_success": False, "block_success": False, "counter_action": agent_response.counter_action,
                    "opposition_index": None}

        if to_challenge:
            action_used: str = action_object.player_action.action
            player_active_cards: set[str] = set(self.players[action_object.active_player_index].state.active_cards())
            allowed_cards: set[str] = set(self.action_player_map[action_used])
            is_valid_move: bool = not allowed_cards.isdisjoint(player_active_cards)
            chosen_cards: list[str] = list(allowed_cards.intersection(player_active_cards))

            if is_valid_move:
                self.players[opposition_index].drop_influence(action_object)
                self.players[action_object.active_player_index].state.switch_with_new(card_to_discard=chosen_cards[-1],
                                                                                      deck=self.deck)
                self.eliminated_cards.append(chosen_cards[-1])
                return {"challenge_success": False, "block_success": False,
                        "counter_action": agent_response.counter_action, "opposition_index": opposition_index}

            agent_action: AgentAction = self.players[action_object.active_player_index].drop_influence(action_object)
            self.eliminated_cards.append(agent_action.card_to_discard)
            return {"challenge_success": True, "block_success": False, "counter_action": agent_response.counter_action,
                    "opposition_index": opposition_index}

        return {"challenge_success": False, "block_success": True, "counter_action": agent_response.counter_action,
                "opposition_index": opposition_index}

    def action_challenge_block(self, action_object: ProcessAction):
        agent_response: AgentAction = self.players[action_object.active_player_index].do_challenge(
            action_object=action_object)
        challenger_index = action_object.active_player_index

        to_challenge: bool = True if agent_response.counter_action == "Challenge" else False

        if not to_challenge:
            return {"challenge_success": False}
        target_index = action_object.player_action.target

        action_used: str = action_object.player_action.action
        player_active_cards: set[str] = set(self.players[target_index].state.active_cards())
        allowed_cards: set[str] = set(self.action_player_map[action_used])
        is_valid_move: bool = not allowed_cards.isdisjoint(player_active_cards)
        chosen_cards: list[str] = list(allowed_cards.intersection(player_active_cards))

        if is_valid_move:
            self.players[challenger_index].drop_influence(action_object)
            self.players[target_index].state.switch_with_new(card_to_discard=chosen_cards[-1], deck=self.deck)
            self.eliminated_cards.append(chosen_cards[-1])
            return {"challenge_success": False}

        agent_action: AgentAction = self.players[target_index].drop_influence(action_object)
        self.eliminated_cards.append(agent_action.card_to_discard)

        return {"challenge_success": True}
