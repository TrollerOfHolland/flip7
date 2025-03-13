# Flip7

Flip7 is a card game simulation project that consists of several components:

- A game server that manages game rounds, player actions, and scores. See [server.py](./server.py).
- Example player implementations in the [example_players](./example_players) folder:
  - [risky.py](./example_players/risky.py) – a player favoring risky moves.
  - [cautious.py](./example_players/cautious.py) – a player with a more cautious strategy.

## How to Run

1. Start the game server:
   ```bash
   python server.py
   ```
2. In separate terminal windows, run one or more of the example players:
   ```bash
   python example_players/risky.py
   ```
   ```bash
   python example_players/cautious.py
   ```
   You can also use [`template_player.py`](./template_player.py) as a starting point to build your own player.

## Game Mechanics

- **Deck Composition:**  
  The deck consists of:
  - **Number Cards:** Cards numbered 0 through 12. The count of each card is equal to its value (except for 0 which appears only once).
  - **Special Action Cards:** Three copies each of `"Freeze!"`, `"Flip Three!"`, and `"Second Chance"`.
  - **Modifier Cards:** One copy each of the modifiers (`+2`, `+4`, `+6`, `+8`, `+10`, and `x2`).

- **Scoring:**  
  Players receive points based on the sum of number cards in their hand. Additional bonus points apply if exactly seven number cards are drawn. Modifier cards can alter the score (e.g., multiplication or addition).

- **Player Actions:**  
  When it's a player's turn, the server sends a decision request (**hit_stay**) along with the player's current hand and the hands of other players.  
  Special action cards trigger targeted actions:
  - **Freeze:** The player must select an active opponent to "freeze" (force them to stay).
  - **Flip Three:** The player chooses an opponent to receive three additional cards.
  - **Second Chance:** This card is used to avoid busting when a duplicate number is drawn.

## Communication Protocol

The game server and players communicate via TCP using JSON-encoded messages.
Below are the key message types:

- **hit_stay**: Server sends a message requesting a decision. The message includes:
  - "hand": the player’s current cards.
  - "hands": all players' hands, indexed by player.
  - Example: `{"action": "hit_stay", "hand": [...], "hands": {...}}`
- **freeze**: When a "Freeze!" card is drawn, the server sends:
  - Example: `{"action": "freeze", "players": ["Player1", "Player2"]}`
  Note that players only contain players that are still active.
- **flip_three**: When a "Flip Three!" card is drawn.
  - Example: `{"action": "flip_three", "players": ["Player1", "Player2"]}`
  Again, players only contain active players.
- **start_game**: Sent by the server to notify players that a round is starting.
  - Example: `{"information": "start_game", "game": 1}`
- **game_over**: Announces the end of a round with a winner.
  - Example: `{"information": "game_over", "winner": "Jorn"}`
- **game_over_final**: Announces the tournament end with final win counts.
  - Example: `{"information": "game_over_final", "win_counts": {"Jorn": 53, "NotJorn": 0}}`
- **ready**: Sent when enough players have joined to start the game.
  - Example: `{"information": "ready", "players": ["Player1", "Player2"]}`
- **stayed**: Indicates a player has chosen to stay.
  - Example: `{"information": "stayed", "player": "Player1"}`
- **busted**: Notifies that a player has busted.
   - Example: `{"information": "busted", "player": "Hugo"}`
- **card_drawn**: Broadcast whenever a card is drawn by any player.
   - Example: `{"information": "card_drawn", "player": "Player1", "card": ["number", 3]}`
- **frozen**: Notifies that a player has been frozen by a Freeze! card.
   - Example: `{"information": "frozen", "player": "Player1", "frozen_by": "Player2"}`
- **flipped 3**: Indicates that a Flip Three! action has been executed.
   - Example: `{"information": "flipped_3", "player": "Player1", "flipped_3_by": "Player2"}`
- **second_chance_used**: Indicates that a Second Chance card was used to avoid a bust.
   - Example: `{"information": "second_chance_used", "player": "Player1"}`

Players should respond by sending JSON messages (encoded as a string) indicating their decisions (e.g., `"hit"`, `"stay"`, or a selected player's name).

## How to Implement Your Own Player

Start with [`template_player.py`](./template_player.py) as a base class. This file contains stub methods (e.g., `handle_hit_stay`, `handle_freeze`, `handle_flip_three`, `handle_information`) that you can override to implement your decision-making logic. For example:

- **Decision Making for hit or stay:**  
  Override `handle_hit_stay` to use your custom logic based on the player's hand.
- **Handling Special Actions:**  
  Override `handle_freeze` and `handle_flip_three` to determine how to target opponents.
- **Processing Game Events:**  
  Override `handle_information` to log game events (such as scores or win notifications) and adjust your strategy accordingly.