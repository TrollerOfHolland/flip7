from net.netimports import *
from FlipGame import *
from config import ELO_FILENAME
import os
import math


class FlipServer(Server):

    games: list[FlipGame] = []
    used_id: list[int] = []
    queue: list[RemotePlayer] = []

    def _add_new_client(self, conn, addr):

        player = RemotePlayer(conn, addr)
        self._clients.append(player)
        self.queue.append(player)

        id = self.get_id()
        player.id = id

        player.send(Message(MessageType.ID_ASSIGN, {"id": id}))


    def create_game(self, player_count):
        new_game = random.sample(self.queue, player_count)
        self.queue = list(set(self.queue) - set(new_game))
        self.games.append(FlipGame(new_game))

    def matcher(self):
        game_target_players = max(3, min(math.ceil(len(self._clients) / 3), 8))

        if(len(self.queue) >= 2*game_target_players):
            self.create_game(int(game_target_players))
        elif(len(self.queue) >= math.ceil(game_target_players*1.5)):
            self.create_game(int(max(math.ceil(game_target_players*0.75), 3)))
        elif(len(self.queue) >= game_target_players):
            self.create_game(len(self.queue))
        pass

    def on_disconnect(self, player: RemotePlayer):
        message = Message(MessageType.DISCONNECT)
        self._parse_message(player, message)

        if(player in self.queue):
            self.queue.remove(player)

        self.used_id.remove(player.id)

        super().on_disconnect(player)


    def _update(self):
        super()._update()
        for game in self.games:

            player_exceeded_time = game.check_decision_time_exceeded()
            if(player_exceeded_time):
                self.on_disconnect(player_exceeded_time)

            if(game.game_over):
                self.queue.extend(game.players)
                self.games.remove(game)
        self.matcher()
        return

    def get_id(self):
        while(True):
            i = random.randint(0, 10000)
            if(i not in self.used_id):
                self.used_id.append(i)
                return i
    
    def get_game_by_player(self, client) -> FlipGame:
        return next((game for game in self.games if client in game.players), None)
    
    def _parse_message(self, player: RemotePlayer, message: Message):

        self.parse_lock.acquire()
        if message.header.type == MessageType.PLAYER_INFO:
            message_json = message.get_json()
            player.set_player_info(message_json["name"], message_json["key"])
        else:
            game = self.get_game_by_player(player)
            if(game):
                game.parse_message(player, message)
        self.parse_lock.release()

    def __init__(self, port, addr="127.0.0.1"):
        self.parse_lock = threading.Lock()
        super().__init__(port, addr)
                    

def main():
    if(not os.path.exists(ELO_FILENAME)):
        with open(ELO_FILENAME, 'w') as write_handle:
            json.dump({}, write_handle, indent=6)


    server = FlipServer(3145)
    server.start_handler()

if __name__ == "__main__":
    main()


    