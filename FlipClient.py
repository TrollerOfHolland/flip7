from net.netimports import *
from Flip import Cards, Player
import random

class FlipClient(Client, Player):
    
    competitors: list[Player] = []

    def _on_connect(self):
        message_json = {"name": self.name, "key": self.elo_key}
        message = Message(MessageType.PLAYER_INFO, message_json)
        self.send(message)
    
    def get_player_by_id(self, id) -> Player:
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
                        competitior = Player()
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
                        print(f"{rank}. Player {k} - {v}points")
                    rank +=1 

            case MessageType.NEW_CARD:
                message_json = message.get_json()
                card = Cards(message_json["card"])
                id = message_json["id"]

                player = self.get_player_by_id(id)
                if(player):
                    player.add_card(card)
            
            case MessageType.BUST:
                message_json = message.get_json()
                player = self.get_player_by_id(message_json["id"])
                player.is_bust = True
                
            case MessageType.STAND:
                message_json = message.get_json()
                player = self.get_player_by_id(message_json["id"])
                player.is_passed = True
            
            case MessageType.FREEZE:
                message_json = message.get_json()
                target = self.get_player_by_id(message_json["to"])
                giver = self.get_player_by_id(message_json["from"])
                target.is_passed = True
                self.on_freeze(giver, target)
            
            case MessageType.FLIP_THREE:
                message_json = message.get_json()
                target = self.get_player_by_id(message_json["to"])
                giver = self.get_player_by_id(message_json["from"])
                self.on_flip_three(giver, target)
            
            case MessageType.SECOND_CHANCE:
                message_json = message.get_json()
                target = self.get_player_by_id(message_json["to"])
                giver = self.get_player_by_id(message_json["from"])
                target.has_second_chance = True
                self.on_second_chance(giver, target)
            
            case MessageType.SECOND_CHANCE_USED:
                message_json = message.get_json()
                target = self.get_player_by_id(message_json["id"])
                target.has_second_chance = False
            
            case MessageType.REQUEST_HIT_OR_STAND:
                hit = self.handle_hit_stand()
                self.send(Message(MessageType.HIT_OR_STAND, {"hit": "T" if hit else "F"}))

            case MessageType.REQUEST_ASSIGN_FREEZE:
                id = self.handle_freeze()
                self.send(Message(MessageType.ASSIGN_FREEZE, {"id": id}))

            case MessageType.REQUEST_ASSIGN_FLIP_THREE:
                id = self.handle_flip_three()
                self.send(Message(MessageType.ASSIGN_FLIP_THREE, {"id": id}))

            case MessageType.REQUEST_ASSIGN_SECOND_CHANCE:
                id = self.handle_second_chance()
                self.send(Message(MessageType.ASSIGN_SECOND_CHANCE, {"id": id}))
            
    def __init__(self, ip: str, port: int, name: str = "Unnamed", elo_key: str = "no_elo"):
        self.name = name
        self.elo_key = elo_key
        super().__init__(ip, port)
        Player.__init__(self)


    

