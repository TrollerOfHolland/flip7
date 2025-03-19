# Flip7

Flip7 is a card game simulation project that consists of several components:

## How to Run

1. Start the game server:
   ```bash
   python FlipServer.py
   ```
2. In separate terminal windows, run one or more of the example players:
   ```bash
   python ExampleCallingStation
   ```
   You can also use [`FlipClient.py`](./FlipClientv.py) as a starting point to build your own player.

## Game Mechanics

- **Deck Composition:**  
  The deck consists of:
  - **Number Cards:** Cards numbered 0 through 12. The count of each card is equal to its value (except for 0 which appears only once).
  - **Special Action Cards:** Three copies each of `"Freeze!"`, `"Flip Three!"`, and `"Second Chance"`.
  - **Modifier Cards:** One copy each of the modifiers (`+2`, `+4`, `+6`, `+8`, `+10`, and `x2`).

- **Scoring:**  
  Players receive points based on the sum of number cards in their hand. Additional bonus points apply if exactly seven number cards are drawn. Modifier cards can alter the score (e.g., multiplication or addition).
  The game ends if a player has more than 200 points by the end of the round. The player with the most points wins the game.

  For this server, players are automatically put into matches, which consist of multiple games.
  The amount of games in a match can be set [in the config](./config.py)
  After each game, the player in 1st place is awarded 1 point, the player in 2nd place is awareded 1/%score decrease ratio% points
  This ratio can also be set in the config file.

  After each game, a players elo rating is automatically updated.
  settings related to elo rating, like the K value and starting elo can also be found [in the config](./config.py)

- **Player Actions:**  
  When it's a player's turn, the server sends a decision request (**hit_stay**) along with the player's current hand and the hands of other players.  
  Special action cards trigger targeted actions:
  - **Freeze:** The player must select an active opponent to "freeze" (force them to stay).
  - **Flip Three:** The player chooses an opponent to receive three additional cards.
  - **Second Chance:** This card is used to avoid busting when a duplicate number is drawn.

## How to Implement Your Own Player

Start with [`FlipClient.py`](./FlipClient.py) as a base class. This file contains stub methods (e.g., `handle_hit_stay`, `handle_freeze`, `handle_flip_three`, `on_freeze`, `on_flip_three`, `on_second_chance`) that you can override to implement your decision-making logic.

If you inherit this base class, as shown in [the example](./ExampleCallingStation.py), You can build your own ai.


Functions whose name starts with `handle`, are called when 
the server expects you to make a decision.

Functions whose name starts with `on`, are functions that are called when the server wants to notify you about an action card being given to another player.
You dont have to implement any of the gamelogic (e.g, you do NOT have to say player.has_second_chance = True when on_second_chance is called), as the client automatically does this, but this information might help you with future decisionmaking.

For clarity, it is advised that you collase the `_parse_message` function, as you only need to modify this method if you want to change the networking 
An important member field for this class is 
* **competitors**. A list of all competitors in the current game.

The FlipClient inherits from Player as given in [Flip.py](./FlipClient.py)
This class contains a number of useful methods for implementing your own client, like
* **get_point_cards()** 
* **get_points()**
Documentation for these methods is provided in the python file itself
The FlipClient also contains a number of member variables, which your ai can use to make decisions
* **is_bust**, a boolean indicating if the player is bust
* **is_frozen**, a boolean indicating if the player is frozen
* **has_second_chance**, a boolean indicating if the player has a second chance card
* **total_points**, a integer indicating the total points the player has in the current game
* **score**, a floating point indicating the total amount of score the player has in the current match