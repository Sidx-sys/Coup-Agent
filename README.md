## Coup-Agent

## Testing Instructions
To test the simulation, run ```python3 main.py```. The default number of players in a game is configured to `3`.
That can be changed using the `num_players` attribute in the `main.py` file.

## TODO
- Add challenge and blocking effects [DONE]
- Different player identities through prompt variations (riskier, safer, random)
- Block failure safety [DONE]
- Enforcing game rules which include enforcing coup once you have more than 10 coins, although that happens naturally.
- Making sure the agent understands the repercussion of challenging [DONE]
- Add challenges, blocks and card losses to history

## Overview

Steps used for creating an agent capable of playing the game "Coup." The agent will be able to:
- Play valid moves.
- Challenge other players' moves.
- Challenge blocks.
- Drop cards smartly.

## Game Overview

### Basic Rules

Coup is a game of deception and strategy where players aim to eliminate each other's influence until only one player remains. The game includes:
- **Characters (Influences)**: Duke, Assassin, Captain, Ambassador, and Contessa.
- **Actions**: Income, Foreign Aid, Coup, Tax, Assassinate, Steal, Exchange.
- **Counteractions**: Blocking Foreign Aid, Blocking Assassination (Contessa), Blocking Stealing (Captain or Ambassador).

### Turn Phases

1. **BeginTurn**: The current player performs an action.
2. **ChallengeAction**: Other players may challenge the action.
3. **BlockAction**: The targeted player may block the action.
4. **ChallengeBlock**: Other players may challenge the block.

## Agent Decision-Making Logic

### 1. Playing Moves

#### Strategy

- **Early Game**: Collect coins (Income or Foreign Aid) to avoid drawing attention.
- **Mid Game**: Use character-specific actions to gain an advantage.
- **Late Game**: Prepare for Coups by collecting coins or eliminating threats.

#### Implementation

1. **Determine Action Priority**: Based on the number of coins and the cards in hand.
2. **Assess Risk**: Consider the likelihood of being challenged or blocked.
3. **Select Action**: Choose the action that maximizes advantage and minimizes risk.

### 2. Challenging Moves

#### Strategy

- **Bluff Detection**: Analyze the history of moves and revealed cards to detect possible bluffs.
- **Risk Assessment**: Weigh the risk of losing an influence against the potential benefit of removing an opponent's influence.

#### Implementation

1. **Analyze Move Legitimacy**: Check the probability that the opponent has the claimed card.
2. **Evaluate Risk vs. Reward**: Decide whether the potential reward of a successful challenge outweighs the risk.
3. **Make Decision**: Challenge if the move is highly suspicious and the risk is acceptable.

### 3. Blocking Moves

#### Strategy

- **Protect Resources**: Block actions that directly harm the agent (e.g., Assassination, Stealing).
- **Consider Challenge**: Assess the likelihood of the block being challenged and the agent's ability to defend the challenge.

#### Implementation

1. **Identify Blockable Actions**: Determine if the agent has the necessary card to block.
2. **Assess Opponent’s Likelihood to Challenge**: Consider the game state and opponent behavior.
3. **Decide to Block or Challenge**: Block if it significantly benefits the agent, otherwise consider challenging the move instead.

### 4. Dropping Cards

#### Strategy

- **Card Value**: Assess the strategic value of each card in hand.
- **Current Game State**: Consider the current game phase and the remaining opponents.
- **Future Potential**: Evaluate the potential future utility of each card.

#### Implementation

1. **Rank Cards**: Based on their utility in the current and future game state.
2. **Evaluate Risks**: Consider which card’s loss would least impact the agent's strategy.
3. **Drop Card**: Choose the card that is least valuable or most expendable.

## Decision-Making Flow

### Begin Turn

1. **Check Coins**: If the agent has 7 or more coins, prepare to Coup.
2. **Select Action**: Based on early, mid, or late game strategy.
3. **Execute Action**: Output the action in JSON format.

### Challenge Action

1. **Analyze History and Eliminated Cards**: Determine the likelihood of a bluff.
2. **Weigh Risks and Rewards**: Decide whether the potential gain is worth the risk.
3. **Make Decision**: Challenge if the risk is acceptable.

### Block Action

1. **Check for Blockable Actions**: Determine if the agent can block.
2. **Assess Risk of Challenge**: Consider the likelihood and consequences of a challenge.
3. **Make Decision**: Block or prepare to challenge if the action seems suspicious.

### Drop Card

1. **Evaluate Card Utility**: Rank the cards based on current and future game states.
2. **Drop Least Valuable Card**: Choose the card with the least strategic value.
