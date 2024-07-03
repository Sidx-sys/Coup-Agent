from state import PlayerState, AgentAction, GameState
from langchain_openai import ChatOpenAI
import json
import re


class Agent:
    def __init__(self, idx: int, card_1: str, card_2: str, llm: ChatOpenAI):
        self.idx: int = idx
        self.llm: ChatOpenAI = llm
        self.state: PlayerState = PlayerState(card_1=card_1, card_2=card_2)
        self.num_moves = 0

        # Prompts
        self.prompts = {}
        with open("prompts/system_prompt.txt") as f:
            self.prompts["system"] = f.read()
        with open("prompts/play_turn.txt") as f:
            self.prompts["play_turn_template"] = f.read()
        with open("prompts/first_turn.txt") as f:
            self.prompts["first_turn_template"] = f.read()
        with open("prompts/drop_influence.txt") as f:
            self.prompts["drop_influence_template"] = f.read()

    def _make_first_move(self, players: list) -> AgentAction:
        active_cards = f"Card 1: {self.state.card_1}, Card 2: {self.state.card_2}"
        coins = self.state.number_of_coins
        first_turn_prompt = self.prompts["first_turn_template"].format(players=players, active_cards=active_cards,
                                                                       coins=coins)
        messages = [("system", self.prompts["system"]), ("human", first_turn_prompt)]
        agent_output = self.llm.invoke(messages).content
        # DEBUG
        print(agent_output)
        # DEBUG
        agent_output = AgentAction(**json.loads(self._clean_json_output(agent_output)))

        return agent_output

    def _make_general_move(self, players: list, history: list[GameState], eliminated_cards: list,
                           opponent_states: list) -> AgentAction:
        active_cards, coins = self._create_agent_state()
        history_text = self._create_history_text(history)
        opponent_states_text = "\n".join(opponent_states)
        play_turn_prompt = self.prompts["play_turn_template"].format(
            players=players,
            game_history=history_text,
            eliminated_cards=eliminated_cards,
            player_index=history[-1].player_index,
            player_action=history[-1].player_action,
            target_player_index=history[-1].target_player_index,
            turn_phase=history[-1].turn_phase,
            active_cards=active_cards,
            coins=coins,
            opponent_states=opponent_states_text
        )

        messages = [("system", self.prompts["system"]), ("human", play_turn_prompt)]
        agent_output = self.llm.invoke(messages).content
        # DEBUG
        print(agent_output)
        # DEBUG
        # todo add retry logic here incase of failures
        agent_output = AgentAction(**json.loads(self._clean_json_output(agent_output)))

        return agent_output

    # def _challenge_move(self):
    #     pass

    def make_move(self, players: list, history: list, eliminated_cards: list, opponent_states: list) -> AgentAction:
        self.num_moves += 1
        if self.num_moves == 1:
            return self._make_first_move(players)

        return self._make_general_move(players, history, eliminated_cards, opponent_states)

    def drop_influence(self, players: list, history: list, eliminated_cards: list, opponent_states: list) -> AgentAction:
        if self.state.num_active_cards() == 1:
            card_to_discard = self.state.card_1 if self.state.card_1_alive else self.state.card_2
            self.state.card_1_alive = self.state.card_2_alive = False
            return AgentAction(card_to_discard=card_to_discard, intuition="Only 1 card left to drop")

        active_cards, coins = self._create_agent_state()
        history_text = self._create_history_text(history)
        opponent_states_text = "\n".join(opponent_states)
        drop_influence_prompt = self.prompts["drop_influence_template"].format(
            players=players,
            game_history=history_text,
            eliminated_cards=eliminated_cards,
            active_cards=active_cards,
            coins=coins,
            opponent_states=opponent_states_text
        )

        messages = [("system", self.prompts["system"]), ("human", drop_influence_prompt)]
        agent_output = self.llm.invoke(messages).content
        agent_output = AgentAction(**json.loads(self._clean_json_output(agent_output)))
        # Discard the influence
        self.state.discard_card(agent_output.card_to_discard)
        return agent_output

    @staticmethod
    def _create_history_text(history: list) -> str:
        history_text = []
        for play in history:
            base_str = f"{play.player_index} used action {play.player_action}"
            if play.target_player_index:
                base_str += f" on {play.target_player_index}"
            history_text.append(base_str)

        return "\n".join(history_text)

    def _create_agent_state(self):
        active_cards = f"Card 1: {self.state.card_1}, Card 2: {self.state.card_2}"
        coins = self.state.number_of_coins
        return active_cards, coins

    @staticmethod
    def _clean_json_output(agent_output: str):
        cleaned_string = re.sub(r'```json|```', '', agent_output).strip()
        return cleaned_string
