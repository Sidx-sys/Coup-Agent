from state import PlayerState, AgentAction, GameState, ProcessAction
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
        with open("prompts/do_challenge.txt") as f:
            self.prompts["do_challenge_template"] = f.read()
        with open("prompts/block_or_challenge.txt") as f:
            self.prompts["block_or_challenge_template"] = f.read()

    def _make_first_move(self, action_object: ProcessAction) -> AgentAction:
        active_cards = f"Card 1: {self.state.card_1}, Card 2: {self.state.card_2}"
        coins = self.state.number_of_coins
        first_turn_prompt = self.prompts["first_turn_template"].format(
            players=action_object.players, index=self.idx, active_cards=active_cards, coins=coins, rounds=action_object.rounds)

        messages = [("system", self.prompts["system"]), ("human", first_turn_prompt)]
        agent_output = self.llm.invoke(messages).content
        # DEBUG
        print(agent_output)
        # DEBUG
        agent_output = AgentAction(**json.loads(self._clean_json_output(agent_output)))

        return agent_output

    def _make_general_move(self, action_object: ProcessAction) -> AgentAction:
        active_cards, coins = self._create_agent_state()
        history_text = self._create_history_text(action_object.history)
        opponent_states_text = "\n".join(action_object.opponent_states)
        play_turn_prompt = self.prompts["play_turn_template"].format(
            players=action_object.players,
            index=self.idx,
            game_history=history_text,
            eliminated_cards=action_object.eliminated_cards,
            player_index=action_object.history[-1].player_index,
            player_action=action_object.history[-1].player_action,
            target_player_index=action_object.history[-1].target_player_index,
            active_cards=active_cards,
            coins=coins,
            opponent_states=opponent_states_text,
            rounds=action_object.rounds
        )

        messages = [("system", self.prompts["system"]), ("human", play_turn_prompt)]
        agent_output = self.llm.invoke(messages).content
        # DEBUG
        print(agent_output)
        # DEBUG
        try:
            agent_output = AgentAction(**json.loads(self._clean_json_output(agent_output)))
        except Exception as e:
            print(e)
            agent_output = AgentAction(action="Income", intuition="Income is always a safe choice")

        return agent_output

    def make_move(self, action_object: ProcessAction) -> AgentAction:
        self.num_moves += 1
        if self.num_moves == 1:
            return self._make_first_move(action_object)

        return self._make_general_move(action_object)

    def drop_influence(self, action_object: ProcessAction) -> AgentAction:
        if self.state.num_active_cards() == 0:
            return AgentAction(card_to_discard=None, intuition="No card left to drop")

        if self.state.num_active_cards() == 1:
            card_to_discard = self.state.card_1 if self.state.card_1_alive else self.state.card_2
            self.state.card_1_alive = self.state.card_2_alive = False
            return AgentAction(card_to_discard=card_to_discard, intuition="Only 1 card left to drop")

        active_cards, coins = self._create_agent_state()
        history_text = self._create_history_text(action_object.history)
        opponent_states_text = "\n".join(action_object.opponent_states)
        drop_influence_prompt = self.prompts["drop_influence_template"].format(
            players=action_object.players,
            game_history=history_text,
            index=self.idx,
            eliminated_cards=action_object.eliminated_cards,
            active_cards=active_cards,
            coins=coins,
            opponent_states=opponent_states_text,
            rounds=action_object.rounds
        )

        messages = [("system", self.prompts["system"]), ("human", drop_influence_prompt)]
        agent_output = self.llm.invoke(messages).content
        agent_output = AgentAction(**json.loads(self._clean_json_output(agent_output)))
        # Discard the influence
        self.state.discard_card(agent_output.card_to_discard)
        return agent_output

    def do_challenge(self, action_object: ProcessAction) -> AgentAction:
        active_cards, coins = self._create_agent_state()
        history_text = self._create_history_text(action_object.history)
        opponent_states_text = "\n".join(action_object.opponent_states)
        do_challenge_prompt = self.prompts["do_challenge_template"].format(
            players=action_object.players,
            index=self.idx,
            game_history=history_text,
            eliminated_cards=action_object.eliminated_cards,
            player_index=action_object.active_player_index,
            player_action=action_object.player_action.action,
            target_player_index=action_object.player_action.target,
            active_cards=active_cards,
            coins=coins,
            opponent_states=opponent_states_text,
            rounds=action_object.rounds
        )

        messages = [("system", self.prompts["system"]), ("human", do_challenge_prompt)]
        agent_output = self.llm.invoke(messages).content
        # DEBUG
        print(agent_output)
        # DEBUG
        # todo add retry logic here incase of failures
        agent_output = AgentAction(**json.loads(self._clean_json_output(agent_output)))

        return agent_output

    def do_block_or_challenge(self, action_object: ProcessAction) -> AgentAction:
        active_cards, coins = self._create_agent_state()
        history_text = self._create_history_text(action_object.history)
        opponent_states_text = "\n".join(action_object.opponent_states)
        do_block_or_challenge_prompt = self.prompts["block_or_challenge_template"].format(
            players=action_object.players,
            index=self.idx,
            game_history=history_text,
            eliminated_cards=action_object.eliminated_cards,
            player_index=action_object.active_player_index,
            player_action=action_object.player_action.action,
            target_player_index=action_object.player_action.target,
            active_cards=active_cards,
            coins=coins,
            opponent_states=opponent_states_text,
            rounds=action_object.rounds
        )

        messages = [("system", self.prompts["system"]), ("human", do_block_or_challenge_prompt)]
        agent_output = self.llm.invoke(messages).content
        # DEBUG
        print(agent_output)
        # DEBUG
        # todo add retry logic here incase of failures
        agent_output = AgentAction(**json.loads(self._clean_json_output(agent_output)))

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
        active_cards_list = [f"Card {idx}: {card}" for idx, card in enumerate(self.state.active_cards())]
        active_cards = ", ".join(active_cards_list)
        coins = self.state.number_of_coins
        return active_cards, coins

    @staticmethod
    def _clean_json_output(agent_output: str):
        cleaned_string = re.sub(r'```json|```', '', agent_output).strip()
        return cleaned_string
