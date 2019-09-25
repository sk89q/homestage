import logging
import random

from sacn import sACNsender
from sacn.sending.output_thread import OutputThread, DEFAULT_PORT


class PatchedOutputThread(OutputThread):
    def send_packet(self, packet, destination: str):
        MESSAGE = bytearray(packet.getBytes())
        try:
            self._socket.sendto(MESSAGE, (destination, DEFAULT_PORT))
            logging.debug(f'Send out Packet to {destination}:{DEFAULT_PORT} with following content:\n{packet}')
        except Exception as e:
            # on suspend or other issues, this will fail
            pass


class PatchedsACNSender(sACNsender):
    def __init__(self, bind_address: str = "0.0.0.0", bind_port: int = DEFAULT_PORT,
                 source_name: str = "default source name", cid: tuple = (), fps: int = 30,
                 universeDiscovery: bool = True):
        super().__init__(bind_address, bind_port, source_name, cid, fps, universeDiscovery)
        if len(cid) != 16:
            cid = tuple(int(random.random() * 255) for _ in range(0, 16))
        self.__CID: tuple = cid

    def start(self, bind_address=None, bind_port: int = None, fps: int = None) -> None:
        if bind_address is None:
            bind_address = self.bindAddress
        if fps is None:
            fps = self._fps
        if bind_port is None:
            bind_port = self.bind_port
        self.stop()
        self._output_thread = PatchedOutputThread(cid=self.__CID, source_name=self.source_name,
                                                  outputs=self._outputs, bind_address=bind_address,
                                                  bind_port=bind_port, fps=fps,
                                                  universe_discovery=self._universeDiscovery)
        self._output_thread.start()
