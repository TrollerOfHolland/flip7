from select import select
from net.netcommon.message import Message, Header, HEADER_SIZE, MAX_SIZE
import threading

class Connection:

    def send(self, message):
        with self.lock:
            self._messages_out.append(message)

    def _parsebytes(self):
        if(self._raw_bytes_in):
            if(not self._message_receiving):
                self._raw_bytes_in, self._message_receiving = Message.from_bytes(
                    self._raw_bytes_in)  # If a message could not be created, this returns(_raw_bytes_in, None)

            if(self._message_receiving):
                self._raw_bytes_in, message_completed = self._message_receiving.load_bytes(
                    self._raw_bytes_in)
                if(message_completed):
                    self.messages_in.append(self._message_receiving)

                    self._message_receiving = None
    

    def update(self):
        self._parsebytes()

        readable, writable, exceptional = select(
            self.io_ctx, self.io_ctx, self.io_ctx, 0.1)

        try:

            for sock in readable:
                new_bytes = (sock.recv(MAX_SIZE))
                self.total_bytes_received += len(new_bytes)
                self._raw_bytes_in += new_bytes


            for sock in writable:
                with self.lock:
                    if(len(self._messages_out) > 0):
                        message = self._messages_out.pop(0)
                        sock.send(bytes(message))

        except Exception as e:
            print(e)
            self.connected = False

    def __init__(self, conn, addr):

        self.connected = True

        self._message_receiving = None   # The message the server is currently trying to receive
        self._raw_bytes_in = b''         # Unparsed bytes
        self.total_bytes_received = 0    # Amount of bytes received

        self.username = ''               # Client local username
        self.ip_addr = ''                # Client ip adress

        self.messages_in = []            # List of unhandled received messages
        self._messages_out = []          # List of all messages that need to be sent
        self._data_messages_out = []     # Same as _messages_out, but has lower priority

        self.lock = threading.Lock()

        self.conn = conn
        self.io_ctx = [self.conn]
        self.addr = addr
