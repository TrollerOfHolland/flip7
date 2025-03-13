import os
import sys
# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from template_player import TemplatePlayer
import random

class BozoPlayer(TemplatePlayer):
    def handle_hit_stay(self, msg):
        # Extract number cards and decide based on sum and presence of a "12"
        numbers = [int(c[1]) for c in msg.get('hand', []) if isinstance(c, list) and c[0] == 'number']
        if sum(numbers) >= 20 and '12' in [c[1] for c in msg.get('hand', []) if isinstance(c, list) and c[0] == 'number']:
            self.send("stay")
        else:
            self.send("hit")
    
    # Use default freeze and flip_three logic from TemplatePlayer.

if __name__ == "__main__":
    player = BozoPlayer(name='Bozo' + str(random.randint(1, 1000)))
    player.play()