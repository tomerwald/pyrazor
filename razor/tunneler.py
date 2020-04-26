from razor.payload import StartTunnel, StopTunnel, RecvOverTunnel, SendOverTunnel
import json


class TunnelException(Exception):
    pass


class RazorTunneler:
    def __init__(self, ip, port, client, timeout=30):
        self.remote_address = f"{ip}:{port}"
        self.timeout = timeout
        self.client = client

    def __enter__(self):
        self.start()

    @staticmethod
    def _check_response(response):
        if response['IsError']:
            raise TunnelException(response["Content"])

    def start(self):
        payload = StartTunnel(self.remote_address, self.timeout).to_razor_payload()
        response = json.loads(self.client.send_receive(payload))
        self._check_response(response)
        print(response["Content"])

    def stop(self):
        payload = StopTunnel().to_razor_payload()
        self.client._initiate_sending()
        self.client.send_buffer(payload)
        # self.client._wait_for_unchoke()
        self.client._finalize_sending()

    def send(self, buf):
        payload = SendOverTunnel(buf).to_razor_payload()
        response = json.loads(self.client.send_receive(payload))
        self._check_response(response)
        return response["Content"]

    def recv(self, n):
        payload = RecvOverTunnel(byte_count=n).to_razor_payload()
        response = json.loads(self.client.send_receive(payload))
        self._check_response(response)
        return bytes.fromhex(response["Content"])

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
