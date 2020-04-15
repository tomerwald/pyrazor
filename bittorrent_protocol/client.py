import struct
from bittorrent_protocol.consts import PROTOCOL_DESCRIPTION


class BitTorrentClient(object):
    def __init__(self, sock, info_hash):
        self.sock = sock
        self.info_hash = info_hash
        self.peer_id = self._generate_peer_id()

    @staticmethod
    def _generate_peer_id():
        return b"-UW109K-LMYpj9A)8X1R"

    def _create_handshake_buffer(self):
        buf = struct.pack("!20s", PROTOCOL_DESCRIPTION)
        buf += b"\x00" * 8  # reserved field
        buf += struct.pack("!20s", self.peer_id)
        buf += struct.pack("!20s", self.info_hash)
        return buf

    def _read_handshake_buffer(self, buf):
        proto = struct.unpack_from("!20s", buf, 0)[0]
        reserve = struct.unpack_from("!8s", buf, 20)[0]
        peer_id = struct.unpack_from("!20s", buf, 28)[0]
        info_hash = struct.unpack_from("!20s", buf, 48)[0]
        return dict(proto=proto, reserve=reserve, peer_id=peer_id, info_hash=info_hash)

    def send_handshake(self):
        buf = self._create_handshake_buffer()
        self.sock.send(buf)
        print("Sent handshake")

    def read_handshake(self):
        print("Waiting for razor handshake")
        buf = self.sock.recv(68)
        return self._read_handshake_buffer(buf)

    def _create_message_buffer(self, message_type, payload):
        length_field = struct.pack("!i", len(payload) + 1)
        buf = length_field + struct.pack("!i", message_type) + payload
        return buf

    # def send
