import random
import socket
import json

# bozo player that always goes for the 7

class RiskyPlayer:
    def __init__(self, name='Risky'):
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('localhost', 5353))
        self.sock.send(self.name.encode())
    
    def play(self):
        file = self.sock.makefile()
        for line in file:
            if not line.strip():
                continue
            msg = json.loads(line)
            if msg.get('action') == 'hit_stay':
                # num_numbers = len([c for c in msg['hand'] if c[0] == 'number'])
                # if num_numbers == 7:
                # # ALWAYS FLIP 7, LUCK IS ON OUR SIDE
                self.sock.send(json.dumps('hit').encode())
            # freeze and flip 3
            elif msg.get('action') == 'freeze':
                options = msg['players']
                if 'Hugo' in options:
                    self.sock.send(json.dumps('Hugo').encode())
                elif len(options) == 1:
                    self.sock.send(json.dumps(options[0]).encode())
                else:
                    options.remove(self.name)
                    self.sock.send(json.dumps(random.choice(options)).encode())
            elif msg.get('action') == 'flip_three':
                # Lmao we pick ourself, WE NEED THE CARDS
                self.sock.send(json.dumps(self.name).encode())
            elif msg.get('information') == 'game_over':
                # This means a game to 200 points has ended.
                print(f"Game Over! Winner: {msg['winner']}")

if __name__ == "__main__":
    player = RiskyPlayer()
    player.play()
