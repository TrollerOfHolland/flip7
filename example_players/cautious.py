import random
import socket
import json

# A perfect example of a nice player with somewhat acceptable code

class CautiousPlayer:
    def __init__(self, name='Cautious'):
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('localhost', 5353))
        self.sock.send(self.name.encode())
    
    def play(self):
        file_obj = self.sock.makefile()  # renamed for clarity
        for line in file_obj:
            if not line.strip():
                continue
            msg = json.loads(line)
            if 'action' in msg:
                match msg['action']:
                    case 'hit_stay':  # Handle hit_stay action
                        if sum(int(c[1]) for c in msg['hand'] if c[0] == 'number') >= 25:
                            self.sock.send(json.dumps('stay').encode())
                        else:
                            self.sock.send(json.dumps('hit').encode())
                    case 'freeze' | 'flip_three':  # Handle freeze and flip_three actions
                        options = msg['players']
                        if 'Hugo' in options:
                            self.sock.send(json.dumps('Hugo').encode())
                        elif len(options) == 1:
                            self.sock.send(json.dumps(options[0]).encode())
                        else:
                            options.remove(self.name)
                            self.sock.send(json.dumps(random.choice(options)).encode())
            elif 'information' in msg:
                match msg['information']:
                    case 'game_over':
                        print(f"Game Over! Winner: {msg['winner']}")
                    case 'game_over_final':
                        print("All games are over!")
                        win_counts = msg['win_counts']
                        for player, wins in win_counts.items():
                            print(f"{player}: {wins} wins")
                    case 'start_game':
                        print(f"Game {msg['game']} has started!")
                    case 'frozen':
                        print(f"{msg['player']} has been frozen by {msg['frozen_by']}")
                    case 'flipped 3':
                        print(f"{msg['player']} has been flipped by {msg['flipped_3_by']}")
                    case 'busted':
                        print(f"{msg['player']} has busted!")
                    case 'second_chance_used':
                        print(f"{msg['player']} has used a second chance!")
                    case 'card_drawn':
                        print(f"{msg['player']} has drawn a {msg['card']}")
                    case 'stayed':
                        print(f"{msg['player']} has stayed!")
                    case 'scores':
                        print("Scores:")
                        for player, score in msg['scores'].items():
                            print(f"{player}: {score}")
                    case _:
                        print("UNKNOWN INFORMATION")
                        print(msg['information'])

if __name__ == "__main__":
    player = CautiousPlayer()
    player.play()