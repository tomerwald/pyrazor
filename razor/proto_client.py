import socket
from bittorrent_protocol.client import BitTorrentClient
from bittorrent_protocol.consts import PROTOCOL_DESCRIPTION
from bittorrent_protocol.message import *
from razor import payload
import os


class BaseRazorPeer(BitTorrentClient):
    def __init__(self, info_hash):
        super(BaseRazorPeer, self).__init__(socket.socket(), info_hash)
        self.block_size = 16384
        self.output_offset = 0
        self.wanted_piece = 12
        self.nonce = None
        self.pending_commands = []

    def _validate_handshake(self, result):
        if result["proto"] != PROTOCOL_DESCRIPTION:
            return False
        elif result["info_hash"] != self.info_hash:
            return False
        else:
            return True

    def _get_one_back_connect(self, address, timeout):
        with socket.socket() as server_sock:
            server_sock.bind(address)
            server_sock.listen(1)
            server_sock.settimeout(timeout)
            client, _ = server_sock.accept()
            return client

    def listen(self, address, timeout=1000):
        self._logger.info(f"Listening for connections on {address}")
        self.sock = self._get_one_back_connect(address, timeout)
        handshake_result = self.read_handshake()
        self.send_handshake()
        self._validate_handshake(handshake_result)
        remote_peer_id = handshake_result["peer_id"]
        self._logger.info(f"Connected to remote peer {remote_peer_id}")

    def connect(self, address):
        self._logger.info(f"Connecting to remote instance on {address}")
        self.sock.connect(address)
        self.send_handshake()
        handshake_result = self.read_handshake()
        self._validate_handshake(handshake_result)
        remote_peer_id = handshake_result["peer_id"]
        self._logger.info(f"Connected to remote peer {remote_peer_id}")

    def send_sequence(self, payload):
        new_message = self.read_message()
        if isinstance(new_message, Request):
            self.sock.send(Piece(new_message.piece_index, new_message.block_offset, payload).create_buffer())

    def request_output(self):
        self.sock.send(Request(12, self.output_offset, self.block_size).create_buffer())
        self.output_offset += self.block_size

    def reject_request(self, req):
        self.sock.send(Reject(req.piece_index, req.block_offset, req.block_length).create_buffer())

    def receive_output(self, enc):
        self.wanted_piece += 1
        self.output_offset = 0
        output = b''
        while True:
            self.request_output()
            new_message = self.read_message()
            if isinstance(new_message, Piece):
                chunk = payload.RazorPayload.read_output(enc.decrypt(new_message.data))
                output += chunk
                try:
                    m = self.read_message(0.1)
                    break
                except Exception as e:
                    pass
            else:
                break
        return output

    def bitfield_handshake(self):
        bitfield = os.urandom(12)
        self.send_bitfield(bitfield)
        self.nonce = bitfield
        self.read_message()
