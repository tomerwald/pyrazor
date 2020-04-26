from razor.payload import StartTunnel, StopTunnel


class TunnelException(Exception):
    pass


class RazorTunneler:
    def __init__(self, ip, port, client, timeout=30):
        self.remote_address = f"{ip}:{port}"
        self.timeout = timeout
        self.client = client

    def __enter__(self):
        self.start()

    def start(self):
        payload = StartTunnel(self.remote_address, self.timeout).to_razor_payload()
        tun_status = self.client.send_receive(payload)
        if tun_status != b'Tunneling':
            raise TunnelException("Failed opening tunnel")
        else:
            print("Tunnel is UP")

    def stop(self):
        payload = StopTunnel().to_razor_payload()
        self.client._initiate_sending()
        self.client.send_buffer(payload)
        # self.client._wait_for_unchoke()
        self.client._finalize_sending()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
