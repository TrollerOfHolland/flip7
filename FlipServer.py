from net.netimports import *
from FlipGame import *
from Flip import BasePlayerInfo
import math


class FlipServer(Server):

    games: list[FlipGame] = []
    used_id: list[int] = []
    queue: list[RemotePlayer] = []
    players: list[RemotePlayer] = []

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
        

    def _add_new_client(self, connection: Connection):
        super()._add_new_client(connection)

        id = self.get_id()

        player = RemotePlayer(connection)
        player.id = id
        self.players.append(player)
        self.queue.append(player)

        message = Message(MessageType.ID_ASSIGN)
        message.push_dict({"id": id})
        connection.send(message)

    def on_disconnect(self, connection: Connection):
        # player = self.get_player_by_connection(client)


        # if(player in self.queue):
        #     self.queue.remove(player)

        # game = self.get_game_by_player(player)
        # if(game):
        #     game.remove_player(player)
        # self.players.remove(player)
        
        message = Message(MessageType.DISCONNECT)
        connection.messages_in.append(message)

    def _update(self):
        for game in self.games:
            if(game.game_over):
                self.queue.extend(game.players)
                self.games.remove(game)
        self.matcher()
        return super()._update()


    def get_id(self):
        for i in range(100000):
            if(i not in self.used_id):
                self.used_id.append(i)
                return i
    
    def get_game_by_player(self, client) -> FlipGame:
        return next((game for game in self.games if client in game.players), None)
    
    def get_player_by_connection(self, connection:Connection) -> RemotePlayer:
        return next((player for player in self.players if player.connection == connection), None)

    def _parse_message(self, connection: Connection, message: Message):

        player = self.get_player_by_connection(connection)
        if message.header.type == MessageType.PLAYER_INFO:
            message_json = message.get_json()
            player.set_name(message_json["name"])
        else:
            game = self.get_game_by_player(player)
            if(game):
                if(not game.parse_message(player, message)):
                    self.players.remove(player)
                    print("removing client")
                    self._clients.remove(player.connection)
                    

def main():
    server = FlipServer(7070)
    server.start_handler()

if __name__ == "__main__":
    main()


    