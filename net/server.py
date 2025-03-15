import socket
import threading
import json
import time

from net.connection import Connection
from net.netcommon.messagetypes import MessageType
from net.netcommon.message import *
from net.netlogger import Logger


class Server:

    _clients: list[Connection] = []
    _running = True
    

    def _add_new_client(self, client: Connection):
        self._clients.append(client)


    def _acceptor(self):
        while self._running:
            try:
                conn, addr = self._socket.accept()
                self._logger.log('New connection ' + str(addr))
            except socket.timeout:
                continue
            client = Connection(conn, addr)
            print("new connection")
            #print(id(client._messages_out))
            self._add_new_client(client)

    def _parse_message(self, client: Connection, message: Message):
        raise NotImplementedError('_parse_return')
    
    def on_disconnect(self, client):
        self._clients.remove(client)

    def _update(self):
        for client in self._clients:
            client.update()

            if not client.connected:
                self.on_disconnect(client)

            if bool(client.messages_in):
                self._parse_message(client, client.messages_in.pop(0))

    def _loop_update(self):
        while self._running:
            self._update()
        

    def amount_of_bytes_received(self):
        count = 0
        for client in self._clients:
            count += client.total_bytes_received

        return count

    def stop(self):
        self._logger.log('Stopping server')
        self._running = False
        self._acceptorThread.join()
        self._handlerThread.join()
        self._socket.close()

    def start_handler(self):
        self._handlerThread = threading.Thread(target=self._loop_update)
        self._handlerThread.start()

    def __init__(self, port, addr="127.0.0.1"):
        self._logger = Logger()

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((addr, port))
        self._socket.settimeout(4)
        self._socket.listen()

        self._acceptorThread = threading.Thread(target=self._acceptor)
        self._acceptorThread.start()
