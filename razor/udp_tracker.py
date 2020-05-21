from enum import Enum
import random
import struct
import socket
import hashlib
import time
from razor.logger import razor_logger


class Action(Enum):
    CONNECT_REQUEST = 0x0
    ANNOUNCE_REQUEST = 0x1
    SCRAPE_REQUEST = 0x2


class ConnectionError(Exception):
    pass


class UDPTrackerAnnouncer(object):
    def __init__(self, ip, port, info_hash, peer_id, peer_port, timeout=1):
        self.ip = ip
        self.port = port
        self._trans_id = 0
        self.connection_id = None
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(timeout)
        self.peer_port = peer_port
        self.logger = razor_logger

    @property
    def transaction_id(self):
        if not self._trans_id:
            self._trans_id = random.randint(0, 255)
        return self._trans_id

    def _create_connection_buffer(self, ):
        protocol_id = 0x41727101980
        action = Action.CONNECT_REQUEST
        buf = struct.pack('!qii', protocol_id, action.value, self.transaction_id)
        return buf

    def _validate_transaction_id(self, result_trans_id):
        if self.transaction_id != result_trans_id:
            raise ConnectionError("Got invalid transaction ID")

    def _parse_connection_response(self, buf):
        action, res_transaction_id = struct.unpack_from("!ii", buf)
        self._validate_transaction_id(res_transaction_id)
        if action == 0x0:
            # successful
            connection_id = struct.unpack_from("!q", buf, 8)[0]
            self.connection_id = connection_id
        if action == 0x3:
            error = struct.unpack_from("!s", buf, 8)
            raise ConnectionError("Tracker responded with error: %s" % error)

    def _send_receive_buffer(self, buf):
        for i in range(5):
            try:
                self.logger.debug("Sending buffer")
                self.sock.sendto(buf, (self.ip, self.port))
                response_buffer, _ = self.sock.recvfrom(128)
            except socket.timeout:
                self.logger.warning("Resending request")
                continue
            return response_buffer
        raise ConnectionError("Retransmission timeout reached")

    def connect(self):
        connection_buffer = self._create_connection_buffer()
        self.logger.debug("Sending connection request")
        response_buffer = self._send_receive_buffer(connection_buffer)
        self.logger.debug("Received connection response")
        self._parse_connection_response(response_buffer)
        self.logger.info("Connected to Tracker on {}".format(self.ip))

    def _create_scrape_buffer(self):
        action = Action.SCRAPE_REQUEST
        buf = struct.pack('!qii20s', self.connection_id, action.value, self.transaction_id, self.info_hash)
        return buf

    def _parse_scrape_response(self, buf):
        action, res_transaction_id = struct.unpack_from("!ii", buf)
        self._validate_transaction_id(res_transaction_id)
        if action == 2:
            # successful
            seeders, completed, leechers = struct.unpack_from("!iii", buf, 8)
            return seeders, leechers, completed
        elif action == 0x3:
            error = struct.unpack_from("!s", buf, 8)
            raise ConnectionError("Tracker responded with error: %s" % error)
        else:
            raise ConnectionError("Tracker responded bad action type: %s" % action)

    def scrape(self):
        scrape_buffer = self._create_scrape_buffer()
        self.logger.debug("Sending scrape request")
        response_buffer = self._send_receive_buffer(scrape_buffer)
        self.logger.debug("Received scrape response")
        self._parse_scrape_response(response_buffer)

    def _create_announce_buffer(self, event):
        action = Action.ANNOUNCE_REQUEST
        buf = struct.pack('!qii', self.connection_id, action.value, self.transaction_id)
        buf += struct.pack("!20s", self.info_hash)
        buf += struct.pack("!20s", self.peer_id)
        buf += struct.pack('!qqq', 0, 0, 2)  # downloaded, left, uploaded
        buf += struct.pack("!iiiih", event, 0, 1231, -1, self.peer_port)  # event, IP, Key, num_want, port
        return buf

    @staticmethod
    def split_ip_field(buf, beginning_offset):
        address_count = int((len(buf) - beginning_offset) / 6)
        addresses = list()
        for i in range(address_count):
            ip = socket.inet_ntoa(buf[beginning_offset + (i * 6):beginning_offset + (i * 6) + 4])
            port = struct.unpack_from("!h", buf, 4 + beginning_offset + (i * 6))[0]
            addresses.append((ip, port))
        return addresses

    def _parse_announce_response(self, buf):
        action, res_transaction_id = struct.unpack_from("!ii", buf)
        self._validate_transaction_id(res_transaction_id)
        if action == 1:
            # successful
            interval, leechers, seeders = struct.unpack_from("!iii", buf, 8)
            addresses = self.split_ip_field(buf, 20)
            return seeders, interval, leechers, addresses
        elif action == 0x3:
            error = struct.unpack_from("!s", buf, 8)
            raise ConnectionError("Tracker responded with error: %s" % error)
        else:
            raise ConnectionError("Tracker responded bad action type: %s" % action)

    def announce(self):
        scrape_buffer = self._create_announce_buffer(2)
        self.logger.debug("Sending announce request")
        response_buffer = self._send_receive_buffer(scrape_buffer)
        self.logger.debug("Received announce response")
        seeders, interval, leechers, addresses = self._parse_announce_response(response_buffer)
        self.logger.debug("Seeders: {}".format(seeders))
        self.logger.info("Leechers: {}".format(leechers))
        self.logger.debug("Peers: {}".format(addresses))

    def _announce_stop(self):
        scrape_buffer = self._create_announce_buffer(3)
        self.logger.info("Sending STOP")
        response_buffer = self._send_receive_buffer(scrape_buffer)

    def __enter__(self):
        self.connect()
        self.announce()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._announce_stop()
