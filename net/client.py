import socket
import socks
import threading
import time
from select import select
from net.netcommon.message import *


class Client:

    _main_thread: threading.Thread = None
    _connected = False
    _running = True

    _is_uploading = False
    _upload_manager = None

    _messages_in = []           # List of unhandled received messages
    _messages_out = []          # List of all messages that need to be sent
    _data_messages_out = []     # Same as _messages_out, but has lower priority
    _message_receiving = None   # The message the server is currently trying to receive

    _raw_bytes_in = b''         # Unparsed bytes
    _proxy = None

    def _on_connect(self):
        pass

    def _connect(self):
        try:
            self.socket = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setblocking(False)
            if(self._proxy):
                self.socket.set_proxy(
                    socks.SOCKS5, self._proxy[0], self._proxy[1])
            self.socket.connect(self.endpoint)
            self.io_ctx = [self.socket]
            self._connected = True
            self._on_connect()
        except Exception as e:
            print(e)

    def _parsebytes(self):
        if(not self._message_receiving):
            self._raw_bytes_in, self._message_receiving = Message.from_bytes(
                self._raw_bytes_in)  # If a message could not be created, this returns(_raw_bytes_in, None)

        if(self._message_receiving):
            self._raw_bytes_in, message_completed = self._message_receiving.load_bytes(
                self._raw_bytes_in)
            if(message_completed):
                self._messages_in.append(self._message_receiving)
                self._message_receiving = None

    def _update(self):
        if (self._raw_bytes_in):
            self._parsebytes()

        readable, writable, exceptional = select(
            self.io_ctx, self.io_ctx, self.io_ctx, 0.1)

        try:
            for sock in readable:
                self._passiveTicks = 0
                self._raw_bytes_in += (sock.recv(MAX_SIZE))

            for sock in writable:
                if(len(self._messages_out) > 0):
                    message = self._messages_out.pop(0)
                    sock.send(bytes(message))
                    continue

                if(len(self._data_messages_out) > 0):
                    message = self._data_messages_out.pop(0)
                    sock.send(bytes(message))

        except Exception as e:
            self._connected = False

    def _parse_message(self, message:Message):
        raise NotImplementedError()

    def _mainloop(self):
        while self._running:
            self._update()
            if(self._messages_in):
                message = self._messages_in.pop(0)
                self._parse_message(message)

    def send(self, message, has_priority=False):
        if(has_priority):
            self._messages_out.insert(0, message)
        else:
            self._messages_out.append(message)

    def start(self):
        self._main_thread = threading.Thread(target=self._mainloop)
        self._main_thread.start()

    def stop(self):
        self._running = False
        self._messages_out.clear()
        if(self._main_thread):
            self._main_thread.join()

    def set_proxy(self, addr, port):
        self.proxy = (addr, port)

    def __init__(self, addr: str, port: int):
        self.endpoint = (addr, port)
