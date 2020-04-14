import socket
import hashlib
from bittorrent_protocol.client import BitTorrentClient


class TortunClient(BitTorrentClient):
    def __init__(self, info_hash):
        super(TortunClient, self).__init__(socket.socket(), info_hash)

    def connect(self, address):
        print(f"Connecting to remote instance on {address}")
        self.sock.connect(address)
        self.send_handshake()


if __name__ == '__main__':
    h = hashlib.sha1()
    h.update(b"tomer")
    t = TortunClient(h.digest())
    t.connect(("127.0.0.1", 6888))
