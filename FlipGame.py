from Flip import Cards, BasePlayerInfo, AddCardResult
from net.netimports import *
from enum import IntEnum
import random


class WrongActionException(Exception):

    def __init__(self, message: str, player: BasePlayerInfo, action: str):       
        self.player = player
        self.action = action
        self.message = message

    def __repr__(self):
        return f"[*] Exception: {self.message}\n player id = {self.player.id}, action: {self.action}"


class Status(IntEnum):
    WAITING = 0
    DECIDING_HIT_OR_STAND = 1
    DECIDING_ASSIGN_FREEZE = 2
    DECIDING_ASSIGN_FLIP_THREE = 3
    DECIDING_ASSIGN_SECOND_CHANCE = 4
    FORCED_HIT = 5
    
class RemotePlayer(BasePlayerInfo):
    opponents: list[BasePlayerInfo] = []
    name: str = ""
    status: Status = Status.WAITING 
    connection: Connection = None
    
    def hit_or_stand(self):
        self.status = Status.DECIDING_HIT_OR_STAND
        message = Message(MessageType.REQUEST_HIT_OR_STAND)
        self.connection.send(message)
    
    def assign_freeze_card(self):

        self.status = Status.DECIDING_ASSIGN_FREEZE
        message = Message(MessageType.REQUEST_ASSIGN_FREEZE)
        self.connection.send(message)


    def assign_flip_three_card(self):
        self.status = Status.DECIDING_ASSIGN_FLIP_THREE
        message = Message(MessageType.REQUEST_ASSIGN_FLIP_THREE)
        self.connection.send(message)

    
    def assign_second_chance_card(self):

        self.status = Status.DECIDING_ASSIGN_SECOND_CHANCE
        message = Message(MessageType.REQUEST_ASSIGN_SECOND_CHANCE)
        self.connection.send(message)
    

    def set_name(self, name: str):
        self.name = name

    def set_id(self, id: int):
        self.id = id

    def __init__(self, connection):
        super().__init__()
        self.connection = connection


class FlipGame:

    def announce(self, message: Message):
        for player in self.players:
            player.connection.send(message)

    def _create_deck(self):
        self.deck = [Cards.ZERO, Cards.PLUS_TWO, Cards.PLUS_FOUR, Cards.PLUS_SIX, Cards.PLUS_EIGHT, Cards.PLUS_TEN, Cards.TIMES_TWO]
        for i in range(1, 13):
            self.deck.extend([Cards(i)] * i)
        
        self.deck.extend([Cards.FREEZE] * 3)
        self.deck.extend([Cards.FLIP_THREE] * 3 )
        self.deck.extend([Cards.SECOND_CHANCE] * 3 )

        random.shuffle(self.deck)
        
    def pop_random_card(self) -> Cards:
        if(not self.deck):
            random.shuffle(self.discards)
            self.deck = self.discards[:]
            self.discards.clear()

        card = random.choice(self.deck)
        self.cards_in_round.append(card)
        self.deck.remove(card)
        return card
        
    def get_player_by_id(self, id) -> RemotePlayer:
        return next((player for player in self.players if player.id == id), None)

    def deal_card(self, player: RemotePlayer):
        if(player.is_bust or player.is_passed or len(player.get_points_cards()) >=7):
            return

        card = self.pop_random_card()

        match(card):
            case Cards.FREEZE:
                self.action_queue.append((player, Status.DECIDING_ASSIGN_FREEZE))
            case Cards.FLIP_THREE:
                self.action_queue.append((player, Status.DECIDING_ASSIGN_FLIP_THREE))
            case Cards.SECOND_CHANCE:
                if(player.has_second_chance):
                    self.action_queue.insert(0, (player, Status.DECIDING_ASSIGN_SECOND_CHANCE))
                else:
                    player.has_second_chance = True


        message = Message(MessageType.NEW_CARD)
        message.push_dict({"id": player.id, "card": card})
        self.announce(message)

        result = player.add_card(card)

        match(result):
            case AddCardResult.BUST:
                message = Message(MessageType.BUST)
                message.push_dict({"id": player.id})
                self.announce(message)
            case AddCardResult.SECOND_CHANCE_USED:
                message = Message(MessageType.SECOND_CHANCE_USED)
                message.push_dict({"id": player.id})
                self.announce(message)

    def get_game_results(self) -> list[(BasePlayerInfo, int)]:
        results = []
        for player in self.players:
            results.append((player, player.total_points))
        results.sort(reverse=True, key= lambda x: x[1])
        return results
    
    def on_game_over(self):
        message = Message(MessageType.GAME_OVER)
        message_json = {}
        results = self.get_game_results()
        for rank in results:
            message_json[rank[0].id] = rank[1]
        message.push_dict(message_json)
        self.announce(message)
        self.game_over = True

    def check_game_over(self)-> bool:
        if(len(self.players) < 3 ):
            self.on_game_over()
        
        for player in self.players:
            if(player.total_points > 200):
                self.on_game_over()
                return True
        return False



    def check_round_over(self):
        alive_players = [player for player in self.players if player.is_alive()]
        if(alive_players):
            return False
        return True
        
    def next_player(self, player):

        index = self.dc_index

        if(self.dc_index != None):
            self.dc_index = None
        else:
            index = self.players.index(player)

        while True:
            print("next player")
            index = (index + 1) % len(self.players)
            player = self.players[index]

            if(player.is_alive()):
                return player
    
    def next_action(self):

        if(self.check_round_over()):
            for player in self.players:
                player.new_round()
            #print("round over")
            if(self.check_game_over()):
                return

            self.start_round()
        elif(self.action_queue):
            action = self.action_queue.pop(0)
            player = action[0]

            if(player not in self.players or not player.is_alive()):
                self.next_action()
                return

            match(action[1]):
                case Status.DECIDING_ASSIGN_FREEZE:
                    self.resolving_player = player
                    player.assign_freeze_card()

                case Status.DECIDING_ASSIGN_FLIP_THREE:
                    self.resolving_player = player
                    player.assign_flip_three_card()

                case Status.DECIDING_ASSIGN_SECOND_CHANCE:
                    valid = [player for player in self.players if (player.is_alive() and not player.has_second_chance)]
                    if(valid and player.has_second_chance):
                        self.resolving_player = player
                        player.assign_second_chance_card()
                    else:
                        self.next_action()

                case Status.FORCED_HIT:
                    self.deal_card(player)
                    self.next_action()

        else:
            self.turn = self.next_player(self.turn)
            if(self.turn in self.players):
                print(f"Waiting for hit / stand of player {self.turn.id}")
                self.turn.hit_or_stand()
            else:
                self.next_action()

    def parse_message(self, player: RemotePlayer, message: Message):

        print(f"[*] Message, id = {player.id} header = {message.header.type}")

        if(message.header.type == MessageType.DISCONNECT):
            self.remove_player(player)
            return False
        
        try:
            player_to_move = self.resolving_player if self.resolving_player else self.turn

            if(player != player_to_move):
                raise WrongActionException("State desync", player, "Not this players turn")
            
            match(message.header.type):
                case MessageType.HIT_OR_STAND:
                    if(player.status == Status.DECIDING_HIT_OR_STAND):

                        message_json = message.get_json()
                        if(message_json["HIT"] == "T"):
                            self.deal_card(player)
                        else:
                            player.is_passed = True
                            message = Message(MessageType.STAND)
                            message.push({"id": player.id})
                            self.announce(message)
                    else:
                        raise WrongActionException("State desync", player, "Hitting")
                    
                    
                case MessageType.ASSIGN_FREEZE:
                    if(player.status == Status.DECIDING_ASSIGN_FREEZE):
                        message_json = message.get_json()
                        target_player_id = message_json["id"]
                        target_player = self.get_player_by_id(target_player_id)

                        if(target_player == None):
                            print("not a fucking player")
                        elif(target_player.is_bust or target_player.is_passed):
                            raise WrongActionException("Wrong target", player, "Cant freeze a player that is already bust or frozen")
                        else: 
                            message = Message(MessageType.FREEZE)
                            message.push_dict({"from": player.id, "to": target_player_id})
                            self.announce(message)
                            target_player.is_passed = True
                    else:
                        raise WrongActionException("State desync", player, "Assign Freeze")
                    
                case MessageType.ASSIGN_FLIP_THREE:
                    if(player.status == Status.DECIDING_ASSIGN_FLIP_THREE):
                        message_json = message.get_json()
                        target_player_id = message_json["id"]
                        target_player = self.get_player_by_id(target_player_id)

                        if(target_player == None):
                            print("not a fucking player")
                        elif(target_player.is_bust or target_player.is_passed):
                            raise WrongActionException("Wrong target", player, "Cant assign flip 3 to a player that is already bust or frozen")
                        else:
                            message = Message(MessageType.FLIP_THREE)
                            message.push_dict({"from": player.id, "to": target_player_id})
                            self.announce(message)
                            for i in range(3):
                                self.action_queue.append((target_player, Status.FORCED_HIT))
                    else:
                        raise WrongActionException("State desync", player, "Flip three")
    
                case MessageType.ASSIGN_SECOND_CHANCE:
                    if(player.status == Status.DECIDING_ASSIGN_SECOND_CHANCE):
                        message_json = message.get_json()
                        target_player_id = message_json["id"]
                        target_player = self.get_player_by_id(target_player_id)

                        if(target_player == None):
                            print("not a fucking player")
                        elif(not target_player.is_alive() or target_player.has_second_chance):
                            raise WrongActionException("Wrong target", player, "Cant assign second chance to a player that is already bust or frozen or has a second chance card")
                        else: 
                            message = Message(MessageType.SECOND_CHANCE)
                            message.push_dict({"from": player.id, "to": target_player_id})
                            self.announce(message)
                            target_player.has_second_chance = True
                    else:
                        raise WrongActionException("State desync", player, "Second Chance")
            self.resolving_player = None
            self.next_action()
            return True
        except WrongActionException as e:
            self.remove_player(player)
            print(e.__repr__())
            self.next_action()
            return False


    
    def start_round(self):
        self.discards.extend(self.cards_in_round)
        self.announce(Message(MessageType.NEW_ROUND))

        self.dealer = self.next_player(self.dealer)
        self.turn = self.dealer

        for player in self.players:
            self.action_queue.append((player, Status.FORCED_HIT))

        self.next_action()

    def remove_player(self, player: RemotePlayer):
        print(f"[!] Player {player.id} disconnected")

        message= Message(MessageType.DISCONNECT)
        message.push_dict({"id": player.id})
        self.announce(message)

        if(self.dealer == player):
            self.dealer = self.next_player(self.dealer)

        if(self.turn == player):
            self.dc_index = self.players.index(player)
            self.players.remove(player)
            self.next_action()
        else:
            self.players.remove(player)




    def __init__(self, players: list[RemotePlayer]):
        self.deck: list[Cards] = []
        self.players: list[RemotePlayer] = players

        self.turn: RemotePlayer
        self.dealer: RemotePlayer = players[0]

        self.resolving_player = None # Used for flip3 -> flip3/freeze/secondchance situations

        self.action_queue: list[tuple[RemotePlayer, Status]] = []
        self.cards_in_round: list[Cards] = [] 
        self.discards: list[Cards] = [] 

        self.game_over = False
        self.dc_index = None


        self.players = players
        self._create_deck()
        print("[*] Creating a new FlipGame, players are: ")
        for player in players:
            player.new_game()
            print(f"{player.name} id = {player.id}, conn = {player.connection.addr}")

        message = Message(MessageType.NEW_GAME)
        message_json = {}
        for i in range(len(players)):
            message_json[i] = players[i].id
        
        message.push_dict(message_json)
        self.announce(message)

        self.start_round()
