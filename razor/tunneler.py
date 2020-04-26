from razor.payload import StartTunnel


class TunnelException(Exception):
    pass


class RazorTunneler:
    def __init__(self, ip, port, client, timeout=30):
        self.remote_address = f"{ip}:{port}"
        self.timeout = timeout
        self.client = client

    def __enter__(self):
        payload = StartTunnel(self.remote_address, self.timeout).to_razor_payload()
        self.client._initiate_sending()
        self.client.send_buffer(payload)
        self.client._wait_for_unchoke()
        self.client._finalize_sending()
        cmd_out = self.client.read_buffer()
        if cmd_out != b'Tunneling':
            raise TunnelException("Failed opening tunnel")

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
