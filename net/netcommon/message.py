import json

HEADER_SIZE = 4
MAX_SIZE = 65535


class Header:

    size = 0
    type = 0

    def __bytes__(self):
        header_raw_bytes = self.type.to_bytes(2, 'big')
        header_raw_bytes += self.size.to_bytes(2, 'big')
        return header_raw_bytes

    @staticmethod
    def from_bytes(header_raw_bytes):
        header = Header()
        header.type = int.from_bytes(header_raw_bytes[0:2], 'big')
        header.size = int.from_bytes(header_raw_bytes[2:4], 'big')
        return header


class Message:

    body: bytes = b""
    _to_receive: int = None

    def push(self, data, raw=False):
        if not raw:
            data = str(data).encode('cp1252')

        self.body += data
        self.header.size = len(self.body)

    def push_dict(self, d, raw=False):
        data = json.dumps(d)
        if not raw:
            data = str(data).encode('cp1252')

        self.body += data
        self.header.size = len(self.body)

    @staticmethod
    def from_bytes(raw_bytes):
        message = Message()

        if(len(raw_bytes) < HEADER_SIZE):  # We do not have enough bytes to create a header
            return raw_bytes, None
        needed_bytes = raw_bytes[:HEADER_SIZE]
        leftover_bytes = raw_bytes[HEADER_SIZE:]
        message.header = Header.from_bytes(needed_bytes)
        message._bytes_still_needed = message.header.size

        return leftover_bytes, message

    def load_bytes(self, raw_bytes):
        bytes_used = raw_bytes[:self._bytes_still_needed]
        leftover_bytes = raw_bytes[self._bytes_still_needed:]

        self.body += bytes_used
        self._bytes_still_needed -= len(bytes_used)

        if(self._bytes_still_needed <= 0):
            return leftover_bytes, True  # Our message was completed

        return leftover_bytes, False    # We still need some data

    def get_json(self) -> dict:
        body_as_string = self.body.decode('cp1252')
        body_as_string = body_as_string.replace('\'', '\"')
        body_as_json = json.loads(body_as_string)
        return body_as_json

    def __bytes__(self):
        message_raw_bytes = bytes(self.header)
        message_raw_bytes += self.body
        return message_raw_bytes

    def __init__(self, type=None):
        self.header = Header()
        if(type):
            self.header.type = type
