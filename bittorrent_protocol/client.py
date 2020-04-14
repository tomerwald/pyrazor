import struct
from bittorrent_protocol.consts import PROTOCOL_DESCRIPTION


class BitTorrentClient(object):
    def __init__(self, sock, info_hash):
        self.sock = sock
        self.info_hash = info_hash
        self.peer_id = self._generate_peer_id()

    @staticmethod
    def _generate_peer_id():
        return b"-UW109K-LMYpj9A)8X0R"

    def _create_handshake_buffer(self):
        buf = struct.pack("!20s", PROTOCOL_DESCRIPTION)
        buf += b"\x00" * 8  # reserved field
        buf += struct.pack("!20s", self.peer_id)
        buf += struct.pack("!20s", self.info_hash)
        return buf

    def send_handshake(self):
        buf = self._create_handshake_buffer()
        self.sock.send(buf)
