import argparse
import logging

from homestage.api import WebServer
from homestage.controller import HomeStage, StageConfig
from homestage.outputs import PatchedsACNSender


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.json')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s (%(levelname)s) [%(name)s] %(message)s",
                        datefmt="%H:%M:%S")
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('socketio.server').setLevel(logging.ERROR)
    logging.getLogger('engineio.server').setLevel(logging.ERROR)

    config = StageConfig(args.config)
    config.load()
    config.save()

    output = PatchedsACNSender(fps=60, bind_address=config.sacn_bind_address)
    output.activate_output(config.sacn_universe)
    output[config.sacn_universe].multicast = config.sacn_multicast
    output[config.sacn_universe].destination = config.sacn_destination
    stage = HomeStage(config, config.fixtures, output)
    server = WebServer(stage)

    stage.start()
    server.start()


if __name__ == '__main__':
    main()
