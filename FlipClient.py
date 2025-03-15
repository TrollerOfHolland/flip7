from net.netimports import *
from Flip import Cards, BasePlayerInfo
import random

class FlipClient(Client, BasePlayerInfo):
    
    competitors: list[BasePlayerInfo] = []

    def _on_connect(self):
        message = Message(MessageType.PLAYER_INFO)
        message_json = {"name": "Larsykfz222 " + str(random.randint(0, 100000)), "pass": "elo"}
        message.push(message_json)
        self.send(message)
    
    def get_player_by_id(self, id) -> BasePlayerInfo:
        if(id == self.id):
            return self
        return next((player for player in self.competitors if player.id == id), 0)
    
    def on_freeze(self, giver, target):
        print(f"{giver.id} gives a freeze to {target.id}")

    def on_flip_three(self, giver, target):
        print(f"{giver.id} gives a flip three to {target.id}")

    def on_second_chance(self, giver, target):
        print(f"{giver.id} gives a second chance to {target.id}")

    def handle_hit_stand(self) -> bool:
        raise NotImplementedError
    
    def handle_freeze(self) -> int:
        raise NotImplementedError
    
    def handle_flip_three(self) -> int:
        raise NotImplementedError
    
    def handle_second_chance(self) -> int:
        raise NotImplementedError

    def _parse_message(self, message: Message):

        match(message.header.type):

            case MessageType.ID_ASSIGN:
                message_json = message.get_json()
                id = int(message_json["id"])
                self.id = id

            case MessageType.NEW_GAME:
                self.new_game()
                self.competitors.clear()
                message_json = message.get_json()
                for k, id in message_json.items():
                    if(id != self.id):
                        competitior = BasePlayerInfo()
                        competitior.id = id
                        self.competitors.append(competitior)

            case MessageType.PLAYER_DISQUALIFIED:
                id = int(message.get_json()["id"])

                if(id == self.id):
                    print("[*] Client is disqualified due to illegal behaviour, quitting")
                    exit()
                else:
                    player = self.get_player_by_id(id)
                    self.competitors.remove(player)

            case MessageType.NEW_ROUND:
                print("new round")
                self.new_round()
                for player in self.competitors:
                    player.new_round()

            case MessageType.GAME_OVER:
                message_json = message.get_json()
                rank = 1
                for k,v in message_json.items():
                    if(k == self.id):
                        print(f"{rank}. You - {v}points")
                    else:
                        print(f"{rank}. player {k} - {v}points")
                    rank +=1 

            case MessageType.NEW_CARD:
                message_json = message.get_json()
                card = Cards(message_json["card"])
                id = message_json["id"]

                player = self.get_player_by_id(id)
                if(player):
                    player.add_card(card)
                return
            
            case MessageType.BUST:
                message_json = message.get_json()
                player = self.get_player_by_id(message_json["id"])
                player.is_bust = True
                return
                
            case MessageType.STAND:
                message_json = message.get_json()
                player = self.get_player_by_id(message_json["id"])
                player.is_passed = True
                return
            
            case MessageType.FREEZE:
                message_json = message.get_json()
                target = self.get_player_by_id(message_json["to"])
                target.is_passed = True

                giver = self.get_player_by_id(message_json["from"])
                self.on_freeze(giver, target)
                return
            
            case MessageType.FLIP_THREE:
                message_json = message.get_json()
                target = self.get_player_by_id(message_json["to"])

                giver = self.get_player_by_id(message_json["from"])
                self.on_flip_three(giver, target)
                return
            
            case MessageType.SECOND_CHANCE:
                message_json = message.get_json()
                target = self.get_player_by_id(message_json["to"])
                target.has_second_chance = True

                giver = self.get_player_by_id(message_json["from"])
                self.on_second_chance(giver, target)
                return
            
            case MessageType.SECOND_CHANCE_USED:
                print("second chance used")
                message_json = message.get_json()
                target = self.get_player_by_id(message_json["id"])
                target.has_second_chance = False
                return
            
            case MessageType.REQUEST_HIT_OR_STAND:
                hit_or_stand = self.handle_hit_stand()
                message = Message(MessageType.HIT_OR_STAND)
                message.push_dict({"HIT": "T"} if hit_or_stand else {"HIT": "F"})
                self.send(message)
                return

            case MessageType.REQUEST_ASSIGN_FREEZE:
                id = self.handle_freeze()
                message = Message(MessageType.ASSIGN_FREEZE)
                message.push_dict({"id": id})
                self.send(message)
                return

            case MessageType.REQUEST_ASSIGN_FLIP_THREE:
                id = self.handle_flip_three()
                message = Message(MessageType.ASSIGN_FLIP_THREE)
                message.push_dict({"id": id})
                self.send(message)
                return

            case MessageType.REQUEST_ASSIGN_SECOND_CHANCE:
                id = self.handle_second_chance()
                message = Message(MessageType.ASSIGN_SECOND_CHANCE)
                message.push_dict({"id": id})
                self.send(message)
                return
            
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)
        BasePlayerInfo.__init__(self)

class LooseyGoosey(FlipClient):

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
    flip_client = LooseyGoosey("127.0.0.1", 7070)
    flip_client._connect()
    flip_client.start()


if __name__ == "__main__":
    main()