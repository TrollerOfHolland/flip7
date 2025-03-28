from Flip import Cards, Player, AddCardResult
from net.netimports import *
from enum import IntEnum
from config import DECISION_TIME, ELO_FILENAME, STARTING_ELO, ELO_K, GAMES_IN_MATCH, SCORE_DECREASE_RATIO
import random

class WrongActionException(Exception):

    def __init__(self, message: str, player: Player, action: str):       
        self.player = player
        self.action = action
        self.message = message

    def __repr__(self):
        return f"[*] Exception: {self.message}\n player id = {self.player.id}, action: {self.action}"



class PlayerElo:

    def _load_elo(self):
        with open(ELO_FILENAME, 'r') as elo_file:
            elo_json: dict[str, int] = json.load(elo_file)
            if(self.key in elo_json.keys()):
                self.elo = elo_json[self.key]
            else:
                self.elo = STARTING_ELO

    def _save_elo(self):
        read_handle =  open(ELO_FILENAME, 'r')
        elo_json: dict[str, int] = json.load(read_handle)
        read_handle.close()
        elo_json[self.key] = self.elo
        write_handle = open(ELO_FILENAME, 'w')
        json.dump(elo_json, write_handle, indent=8)
        write_handle.close()

    def set_elo(self, elo):
        self.elo = elo
        if(self.key != None):
            self._save_elo()

    @staticmethod
    def update_elo(a, b, s_a: float):
        q_a = 10 ** (a.elo / 400)
        q_b = 10 ** (b.elo / 400)
        p_a = q_a / (q_a + q_b)
        p_b = 1 - p_a

        a.set_elo(a.elo + ELO_K * (s_a - p_a))
        b.set_elo(b.elo + ELO_K * ((1-s_a) - p_b))

    @staticmethod
    def update_elos(players):
        for player, px in players.items():
            for opponent, py in players.items():
                if(player == opponent):
                    continue
                PlayerElo.update_elo(player, opponent, int(px > py) if px != py else 0.5)

    def set_key(self, key:str):
        self.key = str(key)
      
    def __init__(self):
        self.key: str = None
        self.elo: int = STARTING_ELO
        pass

class Status(IntEnum):
    WAITING = 0
    DECIDING_HIT_OR_STAND = 1
    DECIDING_ASSIGN_FREEZE = 2
    DECIDING_ASSIGN_FLIP_THREE = 3
    DECIDING_ASSIGN_SECOND_CHANCE = 4
    FORCED_HIT = 5

class RemotePlayer(Player, Connection):

    def hit_or_stand(self):
        self.last_action = time.time()
        self.status = Status.DECIDING_HIT_OR_STAND
        message = Message(MessageType.REQUEST_HIT_OR_STAND)
        self.send(message)
    
    def assign_freeze_card(self):
        self.last_action = time.time()
        self.status = Status.DECIDING_ASSIGN_FREEZE
        message = Message(MessageType.REQUEST_ASSIGN_FREEZE)
        self.send(message)

    def assign_flip_three_card(self):
        self.last_action = time.time()
        self.status = Status.DECIDING_ASSIGN_FLIP_THREE
        message = Message(MessageType.REQUEST_ASSIGN_FLIP_THREE)
        self.send(message)

    def assign_second_chance_card(self):
        self.last_action = time.time()
        self.status = Status.DECIDING_ASSIGN_SECOND_CHANCE
        message = Message(MessageType.REQUEST_ASSIGN_SECOND_CHANCE)
        self.send(message)

    def check_decision_time_exceeded(self, current_time):
        if(self.status == Status.WAITING):
            return False
        
        return ((current_time - self.last_action)*1000) > DECISION_TIME
    
    def set_player_info(self, name: str, key: str):
        self.name = name
        if(key != "no_elo"): self.elo.set_key(key)

    def __init__(self, conn, addr):
        self.opponents: list[Player] = []
        self.name: str = ""
        self.status: Status = Status.WAITING       
        self.last_action: float = 0 
        Connection.__init__(self, conn, addr)
        Player.__init__(self)
        self.elo: PlayerElo = PlayerElo()



class FlipMatch:

    def announce(self, message: Message):
        for player in self.players:
            player.send(message)
    
    def update_scores(self):
        points = sorted([player.total_points for player in self.players], reverse=True)
        for player in self.players: player.score = 1 / (SCORE_DECREASE_RATIO ** points.index(player.total_points))

    def _on_match_over(self):
        results_map = {player.elo: player.score for player in self.players}
        PlayerElo.update_elos(results_map)
        self.match_over = True

    def _on_game_over(self):
        self.announce(Message(MessageType.NEW_GAME))
        self.update_scores()
        for player in self.players:
            player.new_game()


    def check_game_over(self)-> bool:
        if(len(self.players) < 3 ):
            return True

        if([player for player in self.players if (player.total_points > 200)]):
            return True
            
        return False

    def _check_round_over(self):
        alive_players = [player for player in self.players if player.is_alive()]
        if(alive_players):
            return False
        return True
    
    def get_player_by_id(self, id) -> RemotePlayer:
        return next((player for player in self.players if player.id == id), None)

    def _create_deck(self):
        self.deck = [Cards.ZERO, Cards.PLUS_TWO, Cards.PLUS_FOUR, Cards.PLUS_SIX, Cards.PLUS_EIGHT, Cards.PLUS_TEN, Cards.TIMES_TWO]
        for i in range(1, 13):
            self.deck.extend([Cards(i)] * i)
        
        self.deck.extend([Cards.FREEZE] * 3)
        self.deck.extend([Cards.FLIP_THREE] * 3 )
        self.deck.extend([Cards.SECOND_CHANCE] * 3 )



    def _pop_random_card(self) -> Cards:
        if(not self.deck):
            self.deck = self.discards
            self.discards = []

        card = self.deck.pop(random.randrange(len(self.deck)))
        self.cards_in_round.append(card)
        return card
    
    def _deal_card(self, player: RemotePlayer):
        if(player.is_bust or player.is_passed or len(player.get_points_cards()) >=7):
            return

        card = self._pop_random_card()

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

        self.announce(Message(MessageType.NEW_CARD, {"id": player.id, "card": card}))

        result = player.add_card(card)
        match(result):
            case AddCardResult.BUST:
                self.announce(Message(MessageType.BUST, {"id": player.id}))
            case AddCardResult.SECOND_CHANCE_USED:
                self.announce(Message(MessageType.SECOND_CHANCE_USED, {"id": player.id}))
      
    def _next_player(self, player):

        index = self.dc_index

        if(self.dc_index != None):
            self.dc_index = None
        else:
            index = self.players.index(player)

        while True:
            index = (index + 1) % len(self.players)
            player = self.players[index]
            if(player.is_alive()):
                return player
    
    def _next_action(self):
        while(True):
            if(self._check_round_over()):
                for player in self.players:
                    player.new_round()
                if(self.check_game_over()):
                    self.games_played += 1
                    self._on_game_over()
                    if(self.games_played >= GAMES_IN_MATCH):
                        self._on_match_over()
                        break
                else:
                    self._start_round()
                    continue

            elif(self.action_queue):

                player, action = self.action_queue.pop(0)

                if(player not in self.players or not player.is_alive()):
                    continue
                
                match(action):
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
                            continue

                    case Status.FORCED_HIT:
                        self._deal_card(player)
                        continue

                break

            else:
                self.turn = self._next_player(self.turn)
                self.turn.hit_or_stand()
                break

    def _start_round(self):
        self.discards.extend(self.cards_in_round)
        self.announce(Message(MessageType.NEW_ROUND))

        self.dealer = self._next_player(self.dealer)
        self.turn = self.dealer

        for player in self.players:
            self.action_queue.append((player, Status.FORCED_HIT))

    def remove_player(self, player: RemotePlayer):
        print(f"[!] Player {player.id} disconnected")

        self.announce(Message(MessageType.PLAYER_DISQUALIFIED, {"id": player.id}))

        if(self.dealer == player):
            self.dealer = self._next_player(self.dealer)

        if(self.turn == player):
            self.dc_index = self.players.index(player)
            self.players.remove(player)
            self._next_action()
        else:
            self.players.remove(player)

    def parse_message(self, player: RemotePlayer, message: Message):
        if(message.header.type == MessageType.DISCONNECT):
            self.remove_player(player)
            return False
        
        try:
            player_to_move = self.resolving_player if self.resolving_player else self.turn

            if(player != player_to_move):
                raise WrongActionException("State desync", player, "Not this players turn")
            
            if(message.header.type == MessageType.HIT_OR_STAND and Status.DECIDING_HIT_OR_STAND):
                    if(message.get_json()["hit"] == "T"):
                        self._deal_card(player)
                    else:
                        player.is_passed = True
                        self.announce(Message(MessageType.STAND, {"id": player.id}))
                    
            elif(message.header.type == MessageType.ASSIGN_FREEZE and Status.DECIDING_ASSIGN_FREEZE):
                target_id = message.get_json()["id"]
                target_player = self.get_player_by_id(target_id)

                if(target_player == None): pass
                elif(target_player.is_alive()):
                    self.announce(Message(MessageType.FREEZE, json={"from": player.id, "to": target_id} ))
                    target_player.is_passed = True
                else:
                    raise WrongActionException("Wrong target", player, "Cant freeze a player that is already bust or frozen")

            elif(message.header.type == MessageType.ASSIGN_FLIP_THREE and player.status == Status.DECIDING_ASSIGN_FLIP_THREE):
                target_id = message.get_json()["id"]
                target_player = self.get_player_by_id(target_id)

                if(target_player == None): pass
                elif(target_player.is_alive()):
                    self.announce(Message(MessageType.FLIP_THREE, json={"from": player.id, "to": target_id} ))
                    for i in range(3):
                        self.action_queue.append((target_player, Status.FORCED_HIT))
                else:
                    raise WrongActionException("Wrong target", player, "Cant assign flip 3 to a player that is already bust or frozen")

            elif(message.header.type == MessageType.ASSIGN_SECOND_CHANCE and player.status == Status.DECIDING_ASSIGN_SECOND_CHANCE):
                target_id = message.get_json()["id"]
                target_player = self.get_player_by_id(target_id)

                if(target_player == None): pass
                elif(target_player.is_alive() and not target_player.has_second_chance):
                    self.announce(Message(MessageType.SECOND_CHANCE, json={"from": player.id, "to": target_id} ))
                    target_player.has_second_chance = True
                else: 
                    raise WrongActionException("Wrong target", player, "Cant assign second chance to a player that is already bust or frozen or has a second chance card")


            else:
                raise WrongActionException("State desync", player, "tried to perform an action that is not allowed")
                    
            player.status = Status.WAITING
            self.resolving_player = None
            self._next_action()
            return True
        except WrongActionException as e:
            print(e)
            self.remove_player(player)
            self._next_action()
            return False
        
    def check_decision_time_exceeded(self) -> Player:
        current_time = time.time()
        for player in self.players:
            if player in self.players:
                if(player.check_decision_time_exceeded(current_time)):
                    return player
                
    
    def __init__(self, players: list[RemotePlayer]):
        self.deck: list[Cards] = []

        self.turn: RemotePlayer
        self.dealer: RemotePlayer = players[0]

        self.resolving_player = None # Used for flip3 -> flip3/freeze/secondchance situations

        self.action_queue: list[tuple[RemotePlayer, Status]] = []
        self.cards_in_round: list[Cards] = [] 
        self.discards: list[Cards] = [] 

        self.games_played = 0
        self.match_over = False
        self.dc_index = None

        self.players: list[RemotePlayer] = players
        self._create_deck()
        print("[*] Creating a new FlipMatch, players are: ")
        for player in players:
            player.new_match()
            print(f"{player.name} id = {player.id}")

        message = Message(MessageType.NEW_MATCH)
        message_json = {}
        for i in range(len(players)):
            message_json[i] = players[i].id
        
        message.push_dict(message_json)
        self.announce(message)

        self._start_round()
        self._next_action()
