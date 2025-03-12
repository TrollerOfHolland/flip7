# Flip7

Flip7 is a card game simulation project that consists of several components:

- A game server that manages game rounds, player actions, and scores. See [server.py].
- Example player implementations in the [example_players] folder:
  - [risky.py] – a player favoring risky moves.
  - [cautious.py] – a player with a more cautious strategy.

## Project Structure

```
flip7/  
├── server.py  
├── README.md  
└── example_players/  
    ├── risky.py  
    └── cautious.py  
```

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

## Game Mechanics

- **Deck:** The deck includes number cards, special action cards (Freeze!, Flip Three!, and Second Chance) and modifier cards.
- **Scoring:** Scores are calculated based on the number cards drawn, with bonus points if seven number cards are drawn.
- **Player Actions:** Players can choose to hit or stay, or use special actions based on the drawn card.

