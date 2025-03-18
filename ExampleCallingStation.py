import random
from FlipClient import FlipClient

class CallingStation(FlipClient):

    def handle_hit_stand(self) -> bool:
        return True
    
    def handle_freeze(self) -> int:
        valid = [player for player in self.competitors if player.is_alive()]
        return random.choice(valid).id if valid else self.id
    
    def handle_flip_three(self) -> int:
        valid = [player for player in self.competitors if player.is_alive()]
        return random.choice(valid).id if valid else self.id
    
    def handle_second_chance(self) -> int:
        valid = [player for player in self.competitors if (player.is_alive() and not player.has_second_chance)]
        if(valid):
            return random.choice(valid).id
        else:
            for player in self.competitors:
                print(player)
            while(True):
                pass


def main():
    flip_client = CallingStation("127.0.0.1", 3145, random.randint(0, 1000), random.randint(0, 1000))
    flip_client._connect()
    flip_client.start()


if __name__ == "__main__":
    main()