import random
import socket
import json

class TemplatePlayer:
    def __init__(self, name="MyPlayer"):
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('localhost', 5353))
        self.send(self.name)
        

    def send(self, data):
        """Send JSON encoded data to the server."""
        self.sock.sendall(json.dumps(data).encode() + b'\n')

    def recv(self):
        """Receive data from the server."""
        return self.sock.recv(1024).decode().strip()

    def play(self):
        """Main loop: process server messages and react accordingly."""
        file_obj = self.sock.makefile()
        for line in file_obj:
            if not line.strip():
                continue
            msg = json.loads(line)
            # Process message by type
            if 'action' in msg:
                if msg['action'] == 'hit_stay':
                    self.handle_hit_stay(msg)
                elif msg['action'] == 'freeze':
                    self.handle_freeze(msg)
                elif msg['action'] == 'flip_three':
                    self.handle_flip_three(msg)
            elif 'information' in msg:
                self.handle_information(msg)
    
    # --- Methods to make smarter by YOUr ---
    def handle_hit_stay(self, msg):
        """
        Basic hit/stay logic:
        - Extract number cards from hand.
        - Hit if the sum is less than 15, else stay.
        """
        numbers = [c[1] for c in msg.get('hand', []) if isinstance(c, list) and c[0] == 'number']
        total = sum(numbers)
        decision = "hit" if total < 15 else "stay"
        self.send(decision)

    def handle_freeze(self, msg):
        """
        Basic special action logic:
        - Select the first available player for freeze or flip_three actions.
        """
        options = msg['players']
        if 'Hugo' in options:
            choice = 'Hugo'
        elif len(options) == 1:
            choice = options[0]
        else:
            choice = random.choice(options)
        self.send(choice)
    
    def handle_flip_three(self, msg):
        """
        Basic special action logic:
        - Delegate to freeze logic. You can change this to a different strategy.
        """
        self.handle_freeze(msg)

    def handle_information(self, msg):
        """
        Basic information handling:
        - Print all received message details.
        - You could for example, save the score when you receive 'scores' information, to make smarter decisions.
        """
        print("Received message:", msg)
        for key, value in msg.items():
            print(f"{key}: {value}")
    
if __name__ == "__main__":
    player = TemplatePlayer(name='MyPlayer')
    player.play()
