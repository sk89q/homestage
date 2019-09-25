import itertools
import json
import logging
import secrets
import threading
from typing import Optional

import aubio
import soundcard

import homestage.fixtures
from homestage.model import Media, Section, Segment
from homestage.patterns import *

logger = logging.getLogger(__name__)


class StageConfig:
    def __init__(self, path):
        self.path = path
        self.config = {}
        self.debug = False
        self._microphone = None
        self.http_bind_address = '0.0.0.0'
        self.http_port = 8923
        self.http_secret_key = secrets.token_hex(32)
        self.sacn_bind_address = '0.0.0.0'
        self.sacn_multicast = False
        self.sacn_destination = '127.0.0.1'
        self.sacn_universe = 1
        self.fixtures = []

    def load(self):
        try:
            with open(self.path, 'r') as f:
                config = json.load(f)
                if not isinstance(config, dict):
                    raise ValueError('expected config file to be a JSON object')
                self.config = config
        except FileNotFoundError:
            config = {}

        self.debug = bool(config.get('debug', False))
        self.microphone = config.get('microphone', None)

        fixtures_config = config.get('fixtures', [])
        fixtures = []
        for fc in fixtures_config:
            cls = getattr(homestage.fixtures, fc['class'])
            fixture = cls(address=fc.get('address', 0))
            fixtures.append(fixture)
        self.fixtures = fixtures

        http_config = config.get('http', {})
        self.http_bind_address = http_config.get('bind', '0.0.0.0')
        self.http_port = http_config.get('port', 8923)
        self.http_secret_key = http_config.get('key', secrets.token_hex(32))

        outputs_config = config.get('outputs', {})
        sacn_config = outputs_config.get('sACN', {})
        self.sacn_bind_address = sacn_config.get('bind', '0.0.0.0')
        self.sacn_multicast = bool(sacn_config.get('multicast', True))
        self.sacn_destination = sacn_config.get('destination', '127.0.0.1')
        self.sacn_universe = sacn_config.get('universe', 1)

    def save(self):
        self.config.update({
            'debug': self.debug,
            'microphone': self.microphone.id if self.microphone else None,
            'http': {
                'bind': self.http_bind_address,
                'port': self.http_port,
                'key': self.http_secret_key,
            },
            'outputs': {
                'sACN': {
                    'bind': self.sacn_bind_address,
                    'multicast': self.sacn_multicast,
                    'destination': self.sacn_destination,
                    'universe': self.sacn_universe,
                }
            }
        })
        with open(self.path, 'w') as f:
            json.dump(self.config, f, sort_keys=True, indent=2)

    @property
    def microphone(self):
        return self._microphone

    @microphone.setter
    def microphone(self, value):
        if value is None:
            self._microphone = None
        elif isinstance(value, str):
            for mic in self.get_microphones():
                if mic.id == value:
                    self._microphone = mic
                    return
            self._microphone = None
        else:
            self._microphone = value

    def get_microphones(self):
        return soundcard.all_microphones()


class ControlState:
    def __init__(self):
        self.axis0 = [0, 0]
        self.axis1 = [0, 0]
        self.lb = False
        self.rb = False
        self.lt = 0
        self.rt = 0
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.triangle = False
        self.square = False
        self.circle = False
        self.cross = False


class AudioState:
    media = Media()
    current_tempo = 0

    def __init__(self, config: StageConfig, sample_rate=44100, fft_size=1024, block_size=512):
        self.config = config
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.block_size = block_size
        self.tempo = aubio.tempo("default", self.fft_size, self.block_size, self.sample_rate)
        self.beat = False
        self.enabled = False
        self.buffer_size = self.block_size * 2
        self.buffer = np.zeros(self.buffer_size)
        self.band_count = 8
        self.bands = [self.sample_rate * 2 ** (x - self.band_count) for x in range(self.band_count)]
        self.band_windows = [
            (int((lower * self.buffer_size) / self.sample_rate), int((upper * self.buffer_size) / self.sample_rate))
            for lower, upper in zip([0] + self.bands[:-1], self.bands)]
        self.spectrum = np.zeros(self.band_count)
        self.spectrum_history_size = int((self.sample_rate / self.block_size) * 5)
        self.spectrum_history_average_size = int((self.sample_rate / self.block_size) * 0.05)
        self.spectrum_history = [np.zeros(self.spectrum_history_size) for i in range(self.band_count)]
        self.spectrum_adjusted = np.zeros(self.band_count)

    def reset(self, media: Media):
        self.media = media
        logger.info(f"Media change ({media.title}) - danceability: {media.analysis.danceability}, "
                    f"energy: {media.analysis.energy}, "
                    f"valence: {media.analysis.valence}")

    def start(self):
        threading.Thread(target=self._run).start()

    def _run(self):
        while True:
            microphone = self.config.microphone
            if not microphone:
                time.sleep(1)  # no microphone? try again later
                continue
            with microphone.recorder(samplerate=self.sample_rate, channels=1, blocksize=self.block_size) as mic:
                while microphone == self.config.microphone:
                    signal = mic.record(numframes=self.block_size)
                    if self.enabled:
                        signal = signal.flatten().astype('float32', casting='same_kind')
                        self.beat = self.tempo(signal)[0] > 0
                        self.current_tempo = self.tempo.get_bpm()

                        self.buffer = np.roll(self.buffer, self.block_size)
                        self.buffer[:self.block_size] = signal
                        dfft = abs(np.fft.rfft(self.buffer))
                        self.spectrum = [np.average(dfft[lower:upper]) for lower, upper in self.band_windows]
                        for i in range(self.band_count):
                            self.spectrum_history[i] = np.roll(self.spectrum_history[i], 1)
                            self.spectrum_history[i][0] = self.spectrum[i]
                            max_ = self.spectrum_history[i].max(initial=0)
                            if max_ > 0:
                                min_ = self.spectrum_history[i].min(initial=0)
                                self.spectrum_adjusted[i] = min(255, (
                                    np.average(self.spectrum_history[i][:self.spectrum_history_average_size])) / (max_))
                            else:
                                self.spectrum_adjusted[i] = 0


class PatternController:
    media: Media
    section: Optional[Section]
    segment: Optional[Segment]

    def __init__(self, state: AudioState, control: ControlState):
        self.state = state
        self.pattern = ControllablePattern(state, control)
        self.last_media = None
        self.last_section = None
        self.last_segment = None

    def update(self, fixtures):
        media = self.state.media
        position = media.position
        section = media.analysis.sections.at(position) if position else None
        segment = media.analysis.segments.at(position) if position else None

        if self.last_media != media:
            self.last_media = media
            self.pattern.on_media_change(media)

        if self.last_section != section:
            self.last_section = section
            self.pattern.on_section_change(section)

        if self.last_segment != segment:
            self.last_segment = segment
            self.pattern.on_segment_change(segment)

        self.pattern.update(fixtures)


class HomeStage:
    def __init__(self, config: StageConfig, fixtures, output):
        self.config = config
        self.fixtures = fixtures
        self.output = output
        self.state = AudioState(config)
        self.control = ControlState()
        self.controller = PatternController(self.state, self.control)
        self.lock = threading.RLock()
        self._enabled = False
        self.dmx_data = [0] * 512

    def start(self):
        self.enabled = True
        threading.Thread(target=self.run).start()
        self.state.start()

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
                self.output.start()

            if not enabled and self._enabled:
                logger.info("Output disableds")
                self._enabled = False
                self.state.enabled = self._enabled
                self.output.stop()

    def run(self):
        while True:
            if self.enabled:
                self.controller.update(self.fixtures)
                for fixture in self.fixtures:
                    values = fixture.values
                    self.dmx_data[fixture.address:fixture.address + len(values)] = values
                self.output[self.config.sacn_universe].dmx_data = tuple(self.dmx_data)
                time.sleep(0.01)
            else:
                time.sleep(1)
