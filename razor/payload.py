from abc import abstractmethod
import json
import struct
import os
import base64

BLOCK_SIZE = 16384 - 96


class RazorPayload(object):
    COMMAND_TYPE = 0x0

    @abstractmethod
    def _generate_payload(self):
        pass

    # <type><len 4><payload><random>
    def to_razor_payload(self, block_size=BLOCK_SIZE):
        initial_payload = self._generate_payload()
        buf = struct.pack("!ii", self.COMMAND_TYPE, len(initial_payload))
        buf += initial_payload
        buf += os.urandom(block_size - len(initial_payload))
        return buf

    @classmethod
    def read_output(cls, output_buffer):
        _, length = struct.unpack_from("!ii", output_buffer)
        return output_buffer[8:8 + length]


class RunCommand(RazorPayload):
    COMMAND_TYPE = 0x1

    def __init__(self, executable, params):
        super(RunCommand, self).__init__()
        self.executable = executable
        self.params = params

    def _generate_payload(self):
        command = {
            u"ExecutablePath": self.executable,
            u"Params": self.params
        }
        return json.dumps(command).encode()


class UploadFile(RazorPayload):
    COMMAND_TYPE = 0x2

    def __init__(self, file_path, data, append=True):
        super(UploadFile, self).__init__()
        self.file_path = file_path
        self.data = data.hex()
        self.append = append

    def _generate_payload(self):
        command = {
            u"FilePath": self.file_path,
            u"Append": self.append,
            u"Data": self.data
        }
        return json.dumps(command).encode()


class StartTunnel(RazorPayload):
    COMMAND_TYPE = 0x3

    def __init__(self, address, timeout):
        super(StartTunnel, self).__init__()
        self.address = address
        self.timeout = timeout

    def _generate_payload(self):
        command = {
            u"RemoteAddress": self.address,
            u"Timeout": self.timeout
        }
        return json.dumps(command).encode()


class StopTunnel(RazorPayload):
    COMMAND_TYPE = 0x6

    def __init__(self):
        super(StopTunnel, self).__init__()

    def _generate_payload(self):
        return b""
