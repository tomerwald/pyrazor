import socket
import hashlib
from bittorrent_protocol.client import BitTorrentClient
from bittorrent_protocol.consts import PROTOCOL_DESCRIPTION


class TortunClient(BitTorrentClient):
    def __init__(self, info_hash):
        super(TortunClient, self).__init__(socket.socket(), info_hash)

    def _validate_handshake(self, result):
        if result["proto"] != PROTOCOL_DESCRIPTION:
            return False
        elif result["info_hash"] != self.info_hash:
            return False
        else:
            return True

    def connect(self, address):
        print(f"Connecting to remote instance on {address}")
        self.sock.connect(address)
        self.send_handshake()
        handshake_result = self.read_handshake()
        self._validate_handshake(handshake_result)
        remote_peer_id = handshake_result["peer_id"]
        print(f"Connected to remote peer {remote_peer_id}")


if __name__ == '__main__':
    h = hashlib.sha1()
    h.update(b"tomer")
    t = TortunClient(h.digest())
    t.connect(("127.0.0.1", 6888))
    t.sock.recv(128)
