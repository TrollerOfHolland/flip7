import os
import sys
# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from template_player import TemplatePlayer
class RiskyPlayer(TemplatePlayer):
    def handle_hit_stay(self, msg):
        # Always choose to hit, we want the cardz
        self.send("hit")
    
    def handle_flip_three(self, msg):
        # Always choose self in a flip_three situation, we want the cardzzz
        self.send(self.name)
    
    # Use default freeze logic from TemplatePlayer.

    # Ignore the print statements in handle_information
    def handle_information(self, msg):
        pass

if __name__ == "__main__":
    player = RiskyPlayer(name='Risky')
    player.play()
