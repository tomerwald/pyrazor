import struct as st
from bittorrent_protocol.consts import MessageTypes


class Message(object):
    MSG_TYPE = 0

    def __init__(self, payload_buffer):
        self.payload_buffer = payload_buffer

    @classmethod
    def from_bytes(cls, buf):
        return cls(buf)

    def create_buffer(self):
        length_field = st.pack("!i", len(self.payload_buffer) + 1)
        return length_field + st.pack("!b", self.MSG_TYPE) + self.payload_buffer


class Request(Message):
    MSG_TYPE = MessageTypes.Request

    def __init__(self, piece_index, block_offset, block_length):
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block_length = block_length
        payload_buffer = st.pack('!iii', piece_index, block_offset, block_length)
        super(Request, self).__init__(payload_buffer)

    @classmethod
    def from_bytes(cls, buf):
        return cls(*st.unpack_from('!iii', buf))


class Bitfield(Message):
    MSG_TYPE = MessageTypes.Bitfield

    def __init__(self, payload_buffer):
        super(Bitfield, self).__init__(payload_buffer)
        self.bitfield = payload_buffer


class Have(Message):
    MSG_TYPE = MessageTypes.Have

    def __init__(self, payload_buffer):
        super(Have, self).__init__(payload_buffer)
        self.piece_index = st.unpack_from('!i', self.payload_buffer)[0]


class UnChoke(Message):
    MSG_TYPE = MessageTypes.Unchoke

    def __init__(self):
        super(UnChoke, self).__init__(b'')


class Choke(Message):
    MSG_TYPE = MessageTypes.Choke

    def __init__(self):
        super(Choke, self).__init__(b'')


class Interested(Message):
    MSG_TYPE = MessageTypes.Unchoke

    def __init__(self):
        super(Interested, self).__init__(b'')


class Piece(Message):
    MSG_TYPE = MessageTypes.Piece

    def __init__(self, piece_index, block_offset, data):
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.data = data
        payload_buffer = st.pack('!ii', piece_index, block_offset) + data
        super(Piece, self).__init__(payload_buffer)

    @classmethod
    def from_bytes(cls, buf):
        piece_index, block_offset = st.unpack_from('!ii', buf, 0)
        data = buf[8:]
        return cls(piece_index, block_offset, data)


_message_classes = [Request, Have, Bitfield, Piece, UnChoke, Choke, Interested]


def parse_message(msg_buf):
    type_to_class = {c.MSG_TYPE: c for c in _message_classes}
    msg_type = st.unpack_from("!b", msg_buf)[0]
    if msg_type in type_to_class:
        if len(msg_buf) > 1:
            return type_to_class[msg_type].from_bytes(msg_buf[1:])
        else:
            return type_to_class[msg_type].from_bytes()
    else:
        raise KeyError(f"Unknown message type:{msg_type}")
