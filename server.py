import socket
import threading
import json
import random
from collections import defaultdict

NUM_GAMES = 10
NUMBER_OF_PLAYERS = 2

class Game:
    """Manages game state and gameplay rounds for Flip7."""
    def __init__(self):
        self.players = []
        self.deck = []
        self.scores = defaultdict(int)
        self.lock = threading.Lock()
        self.game_active = False

    def create_deck(self):
        """Creates, shuffles, and returns a new deck excluding players' current cards."""
        deck = []
        for number in range(0, 13):
            for _ in range(number if number != 0 else 1):
                deck.append(('number', number))
        for _ in range(3):
            deck.append(('action', 'Freeze!'))
            deck.append(('action', 'Flip Three!'))
            deck.append(('action', 'Second Chance'))
        modifiers = ['+2', '+4', '+6', '+8', '+10', 'x2']
        for mod in modifiers:
            deck.append(('modifier', mod))
        for p in self.players:
            for card in p.hand:
                deck.remove(card)
        random.shuffle(deck)
        return deck

    def start_game(self):
        """Starts multiple rounds of the game and announces final results."""
        with self.lock:
            self.game_active = True
        win_counts = defaultdict(int)
        for game_index in range(NUM_GAMES):
            for p in self.players:
                p.send(json.dumps({'information': 'start_game', 'game': game_index + 1}))
            print(f"Game {game_index + 1}")
            self.scores = defaultdict(int)
            self.deck = []
            for p in self.players:
                p.reset()
            while True:
                self.play_round()
                winner = self.check_winner()
                if winner is not None:
                    self.announce_winner(winner)
                    win_counts[winner] += 1
                    break
        final_msg = json.dumps({'information': 'game_over_final', 'win_counts': dict(win_counts)})
        for p in self.players:
            p.send(final_msg)
        print("Over!")
        for p, c in win_counts.items():
            print(f"Player {p} won {c} games")
        with self.lock:
            self.game_active = False

    def play_round(self):
        """Executes a round: deals cards, handles player actions, and calculates scores."""
        players = self.players.copy()
        # Reset player states
        for p in players:
            p.reset()
        # Deal initial card
        for p in players:
            if not self.deck:
                self.deck = self.create_deck()
            card = self.deck.pop()
            self.resolve_card(p, card)
        # Players take turns
        while True:
            for p in players:
                if p.busted or p.stayed:
                    continue
                # Send current state
                p.send(json.dumps({
                    'action': 'hit_stay',
                    'hand': p.hand,
                    'hands': {pl.id: pl.hand for pl in players}
                }))
                # Get decision
                try:
                    decision = json.loads(p.recv())
                    if decision == 'hit':
                        if not self.deck:
                            self.deck = self.create_deck()
                        card = self.deck.pop()
                        self.resolve_card(p, card)
                    else:
                        p.stayed = True
                        for pl in players:
                            pl.send(json.dumps({'information': 'stayed', 'player': p.id}))
                except:
                    p.busted = True
                    for pl in players:
                        pl.send(json.dumps({'information': 'busted', 'player': p.id}))
                if any(len([c for c in p.hand if c[0] == 'number']) == 7 for p in players):
                    break
            if all(p.busted or p.stayed for p in players) or any(len([c for c in p.hand if c[0] == 'number']) == 7 for p in players):
                break
        # Calculate scores
        for p in players:
            if not p.busted:
                total = sum(c[1] for c in p.hand if c[0] == 'number')
                if 'x2' in p.modifiers:
                    total *= 2
                for mod in p.modifiers:
                    if mod.startswith('+'):
                        total += int(mod[1:])
                num_numbers = len([c for c in p.hand if c[0] == 'number'])
                if num_numbers == 7:
                    total += 15
                self.scores[p.id] += total
        # send scores
        for p in self.players:
            p.send(json.dumps({'information': 'scores', 'scores': self.scores}))

    def resolve_card(self, player, card):
        """Processes a drawn card, updating player state and handling special action/modifier effects."""
        player.hand.append(card)
        for p in self.players:
            p.send(json.dumps({'information': 'card_drawn', 'player': player.id, 'card': card}))
        if card[0] == 'action':
            if card[1] == 'Freeze!':
                player.send(json.dumps({'action': 'freeze', 'players': [p.id for p in self.players if not p.busted and not p.stayed]}))
                try:
                    frozen_player = json.loads(player.recv())
                    found = False
                    for p in self.players:
                        if p.id == frozen_player:
                            p.stayed = True
                            found = True
                            for pl in self.players:
                                pl.send(json.dumps({'information': 'frozen', 'player': p.id, 'frozen_by': player.id}))
                            break
                    if not found:
                        player.stayed = True
                        for p1 in self.players:
                            p1.send(json.dumps({'information': 'frozen', 'player': player.id, 'frozen_by': player.id}))
                except:
                    player.stayed = True
                    for p in self.players:
                        p.send(json.dumps({'information': 'frozen', 'player': player.id, 'frozen_by': player.id}))
            elif card[1] == 'Flip Three!':
                player.send(json.dumps({'action': 'flip_three', 'players': [p.id for p in self.players if not p.busted and not p.stayed]}))
                try:
                    flipped_player = json.loads(player.recv())
                    found = False
                    for p in self.players:
                        if p.id == flipped_player:
                            for pl in self.players:
                                pl.send(json.dumps({'information': 'flipped 3', 'player': p.id, 'flipped_3_by': player.id}))
                            # flip 3 cards for the player, while he is not busted
                            for _ in range(3):
                                if p.busted or p.stayed or len([c for c in p.hand if c[0] == 'number']) == 7:
                                    break
                                if not self.deck:
                                    self.deck = self.create_deck()
                                card = self.deck.pop()
                                self.resolve_card(p, card)
                            found = True
                            break
                    if not found:
                        for pl in self.players:
                            pl.send(json.dumps({'information': 'flipped 3', 'player': flipped_player, 'flipped_3_by': player.id}))
                        for _ in range(3):
                            if player.busted or player.stayed or len([c for c in player.hand if c[0] == 'number']) == 7:
                                break
                            if not self.deck:
                                self.deck = self.create_deck()
                            card = self.deck.pop()
                            self.resolve_card(player, card)
                except:
                    for pl in self.players:
                        pl.send(json.dumps({'information': 'flipped 3', 'player': player.id, 'flipped_3_by': player.id}))
                    for _ in range(3):
                        if player.busted or player.stayed or len([c for c in player.hand if c[0] == 'number']) == 7:
                            break
                        if not self.deck:
                            self.deck = self.create_deck()
                        card = self.deck.pop()
                        self.resolve_card(player, card)
            elif card[1] == 'Second Chance':
                if 'Second Chance' not in player.action_cards:
                    player.action_cards.append('Second Chance')
        elif card[0] == 'modifier':
            player.modifiers.append(card[1])
        
        # Check for number duplicates
        nums = [c[1] for c in player.hand if c[0] == 'number']
        duplicates = any(nums.count(num) > 1 for num in nums)
        if duplicates and 'Second Chance' not in player.action_cards:
            for pl in self.players:
                pl.send(json.dumps({'information': 'busted', 'player': player.id}))
            player.busted = True
        elif duplicates:
            for pl in self.players:
                pl.send(json.dumps({'information': 'second_chance_used', 'player': player.id}))
            player.action_cards.remove('Second Chance')

    def check_winner(self):
        """Determines if any player's score reaches the win threshold."""
        if not self.scores:
            return None
        max_score = max(self.scores.values())
        if max_score < 200:
            return None
        winners = [pid for pid, score in self.scores.items() if score == max_score]
        if len(winners) == 1:
            return winners[0]
        else:
            return None

    def announce_winner(self, winner):
        """Notifies all players about the game over outcome, announcing the winner."""
        for p in self.players:
            p.send(json.dumps({'information': 'game_over', 'winner': winner}))

class PlayerHandler:
    """Handles communication and game participation for a single player."""
    def __init__(self, conn, addr, game):
        self.conn = conn
        self.addr = addr
        self.game = game
        self.id = None
        self.hand = []
        self.modifiers = []
        self.action_cards = []
        self.busted = False
        self.stayed = False

    def reset(self):
        """Resets the player's hand and state for a new round."""
        self.hand = []
        self.modifiers = []
        self.action_cards = []
        self.busted = False
        self.stayed = False

    def send(self, data):
        """Sends data over the player's connection."""
        try:
            self.conn.sendall(data.encode() + b'\n')
        except BrokenPipeError:
            print(f"Broken pipe when sending to {self.id}. Removing client.")
            # Optionally remove client from the game.
            with self.game.lock:
                if self in self.game.players:
                    self.game.players.remove(self)
        except Exception as e:
            print(f"Unexpected error when sending to {self.id}: {e}")

    def recv(self):
        """Receives data from the player's connection."""
        return self.conn.recv(1024).decode().strip()

    def handle(self):
        """Processes the player's connection, registers their ID, and starts the game when ready."""
        self.id = self.recv()
        with self.game.lock:
            self.game.players.append(self)
        if len(self.game.players) >= NUMBER_OF_PLAYERS and not self.game.game_active:
            for p in self.game.players:
                p.send(json.dumps({
                    'information': 'ready',
                    'players': [pl.id for pl in self.game.players]
                }))
            self.game.start_game()

def main():
    """Initializes the TCP server, listens for incoming connections, and spawns new player handlers."""
    host = 'localhost'
    port = 5353
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    game = Game()
    print(f"Server listening on {host}:{port}")
    while True:
        conn, addr = server.accept()
        handler = PlayerHandler(conn, addr, game)
        threading.Thread(target=handler.handle).start()

if __name__ == "__main__":
    main()