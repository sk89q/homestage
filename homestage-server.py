import argparse
import logging

import sacn

import config
from homestage.api import WebServer
from homestage.controller import AudioState, HomeStage


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s (%(levelname)s) [%(name)s] %(message)s",
                        datefmt="%H:%M:%S")
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    sender = sacn.sACNsender(fps=120)
    sender.activate_output(1)
    sender[1].multicast = config.SACN_MULTICAST
    sender[1].destination = config.SACN_HOST

    listener = AudioState(config.RECORDING_DEVICE)
    stage = HomeStage(config.DEVICES, sender, listener)
    server = WebServer(stage, config.WEB_SERVER_HOST, config.WEB_SERVER_PORT)

    listener.start()
    stage.start()
    server.start()


if __name__ == '__main__':
    main()
