import itertools
import logging
import threading
from typing import Optional

import aubio

from homestage.model import Media, Section
from homestage.patterns import *

logger = logging.getLogger(__name__)


class AudioState:
    media = Media()
    current_tempo = 0

    def __init__(self, mic, sample_rate=44100, fft_size=1024, block_size=512):
        self.mic = mic
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.block_size = block_size
        self.tempo = aubio.tempo("default", self.fft_size, self.block_size, self.sample_rate)
        self.beat = False
        self.enabled = False

    def reset(self, media: Media):
        self.media = media
        logger.info(f"Media change ({media.title}) - danceability: {media.analysis.danceability}, "
                    f"energy: {media.analysis.energy}, "
                    f"valence: {media.analysis.valence}")

    def start(self):
        threading.Thread(target=self._run).start()

    def _run(self):
        with self.mic.recorder(samplerate=self.sample_rate, channels=1) as mic:
            while True:
                signal = mic.record(numframes=self.block_size)
                if self.enabled:
                    signal = signal.flatten().astype('float32', casting='same_kind')
                    self.beat = self.tempo(signal)[0] > 0
                    self.current_tempo = self.tempo.get_bpm()


class PatternController:
    media: Media
    section: Optional[Section]

    def __init__(self, state: AudioState):
        self.state = state
        self.pattern = RainbowSweep(state)
        self.media = Media()
        self.section = None
        self.bank = [
            lambda: DualToneResponseFastSweep(self.state),
            lambda: RainbowSweep(self.state),
            lambda: MellowSweep(self.state),
        ]

    def get_pattern(self, media) -> Pattern:
        position = media.position
        change = False

        if self.media != media:
            self.media = media
            change = True

        if position:
            section = media.analysis.sections.at(position)
            if self.section != section:
                self.section = section
                change = True
        else:
            self.section = None

        if change:
            self.pattern = random.choice(self.bank)()
            logger.info("Change of pattern triggered")

        return self.pattern


class HomeStage:
    def __init__(self, devices, sender, state: AudioState):
        self.devices = devices
        self.sender = sender
        self.state = state
        self.controller = PatternController(state)
        self.lock = threading.RLock()
        self._enabled = False

    def start(self):
        self.enabled = True
        threading.Thread(target=self.run).start()

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        with self.lock:
            if enabled and not self._enabled:
                logger.info("Output enabled")
                self._enabled = True
                self.state.enabled = self._enabled
                self.sender.start()

            if not enabled and self._enabled:
                logger.info("Output disableds")
                self._enabled = False
                self.state.enabled = self._enabled
                self.sender.stop()

    def run(self):
        while True:
            if self.enabled:
                pattern = self.controller.get_pattern(self.state.media)
                pattern.update(self.devices)
                self.sender[1].dmx_data = tuple(itertools.chain(*[d.values for d in self.devices]))
                time.sleep(0.01)
            else:
                time.sleep(1)
