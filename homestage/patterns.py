import random
import time
from colorsys import hsv_to_rgb

import math
import numpy as np


def cycle(f):
    return (math.sin(time.time() / math.pi * 2 * f) + 1) / 2


class Pattern:
    def update(self, fixtures):
        return False

    def on_media_change(self, media):
        pass

    def on_section_change(self, section):
        pass

    def on_segment_change(self, segment):
        pass


class DelegatePattern:
    def __init__(self, delegate):
        self.delegate = delegate

    def on_media_change(self, media):
        self.delegate.on_media_change(media)

    def on_section_change(self, section):
        self.delegate.on_section_change(section)

    def on_segment_change(self, segment):
        self.delegate.on_segment_change(segment)

    def update(self, fixtures):
        self.delegate.update(fixtures)


class RainbowRoundabout(Pattern):
    def __init__(self, state, control):
        self.state = state
        self.control = control
        self.index = 0
        self.last_beat = time.time()
        self.tempo_beat = 0

    def on_segment_change(self, segment):
        self.index += 0.2 * math.log(segment.duration * 10)

    def update(self, fixtures):
        now = time.time()
        color = hsv_to_rgb(math.sin(self.index) / 2 + 0.5, 1, 1)

        for i, fixture in enumerate(fixtures):
            active = True
            fixture.pan = int((cycle(4) / 6 + 2 / 6) * (2 / 3 * 255))
            # fixture.tilt = int((cycle(2) / 8 + 7 / 8) * 255)
            fixture.tilt = int((cycle(2) / 8 + 5 / 8) * 255)
            fixture.r = int(255 * color[0])
            fixture.g = int(255 * color[1])
            fixture.b = int(255 * color[2])
            fixture.level = int(134)
            fixture.level = min(134, int(134 * np.average(self.state.spectrum_adjusted[:2]))) if active else 0
            fixture.brightness = int(255 * np.average(self.state.spectrum_adjusted[:2])) if active else 0
            fixture.motor1 = int((math.sin(time.time() / 0.7) * 255 / 2 + 255 / 2))
            fixture.motor2 = int((math.sin(time.time() / 0.7) * 255 / 2 + 255 / 2))

        self.index += 0.01

        if self.state.current_tempo and (now - self.last_beat) > 1 / self.state.current_tempo:
            self.tempo_beat += 1 / len(fixtures) / 8
            self.last_beat = now

        return False


class RainbowCycle(Pattern):
    def __init__(self, state, control):
        self.state = state
        self.control = control
        self.index = 0

    def on_segment_change(self, segment):
        self.index += 0.2 * math.log(segment.duration * 10)

    def update(self, fixtures):
        for i, fixture in enumerate(fixtures):
            color = hsv_to_rgb(math.sin(self.index + (i / len(fixtures) * 3)) / 2 + 0.5, 1, 1)
            fixture.pan = int((cycle(4) / 6 + 2 / 6) * (2 / 3 * 255))
            # fixture.tilt = int((cycle(2) / 8 + 7 / 8) * 255)
            fixture.tilt = int((cycle(2) / 8 + 5 / 8) * 255)
            fixture.r = int(255 * color[0])
            fixture.g = int(255 * color[1])
            fixture.b = int(255 * color[2])
            fixture.level = int(134)
            fixture.level = max(0, min(134, int(134 * self.state.spectrum_adjusted[1])))
            fixture.brightness = max(0, min(255, int(255 * self.state.spectrum_adjusted[1])))
            fixture.motor1 = int((math.sin(time.time() / 0.7) * 255 / 2 + 255 / 2))
            fixture.motor2 = int((math.sin(time.time() / 0.7) * 255 / 2 + 255 / 2))

        self.index += 0.01
        return False


class BloodPumper(Pattern):
    def __init__(self, state, control):
        self.state = state
        self.control = control
        self.fixture_index = 0
        self.last_interval = 0

    def update(self, fixtures):
        now = time.time()
        factor = 10 if self.control.lb else 20
        if now - self.last_interval > factor / (self.state.current_tempo or 100):
            self.last_interval = now
            self.fixture_index += 1
            if self.fixture_index >= len(fixtures):
                self.fixture_index = 0
            target = fixtures[self.fixture_index]
            for fixture in fixtures:
                color = (1, 1, 1) if target == fixture else (0, 0, 0)
                fixture.pan = int((cycle(4) / 3 + 1 / 3) * (2 / 3 * 255))
                fixture.tilt = int((cycle(2) / 3 + 1 / 3) * 255)
                fixture.r = int(255 * color[0])
                fixture.g = int(255 * color[1])
                fixture.b = int(255 * color[2])
                fixture.level = int(134)
                fixture.brightness = 255

        return False


class ControllablePattern(DelegatePattern):
    def __init__(self, state, control):
        super().__init__(RainbowRoundabout(state, control))
        self.delegate_enabled = True
        self.state = state
        self.control = control
        self.pan = 0
        self.tilt = 0
        self.rgb = [255, 255, 255]

    def update(self, fixtures):
        if self.control.square:
            self.delegate_enabled = True
            if not isinstance(self.delegate, RainbowRoundabout):
                self.delegate = RainbowRoundabout(self.state, self.control)
        elif self.control.circle:
            self.delegate_enabled = True
            if not isinstance(self.delegate, BloodPumper):
                self.delegate = BloodPumper(self.state, self.control)
        elif self.control.cross:
            self.delegate_enabled = True
            if not isinstance(self.delegate, RainbowCycle):
                self.delegate = RainbowCycle(self.state, self.control)
        elif self.control.triangle:
            self.delegate_enabled = False

        super().update(fixtures)

        if not self.delegate_enabled:
            if self.control.lb:
                x0 = self.control.axis0[1]
                y0 = self.control.axis0[0]
                h = (math.atan2(y0, x0) + math.pi) / math.tau
                v = math.sqrt(x0 ** 2 + y0 ** 2)
                if v < 0.1:
                    v = 0
                else:
                    v = (v - 0.1) / (1 - 0.1)
                self.rgb = [int(255 * n) for n in hsv_to_rgb(h, 1, min(1, v))]

            if self.control.rb:
                x1 = self.control.axis1[1]
                y1 = self.control.axis1[0]
                pan = (math.atan2(y1, x1) + math.pi) / math.tau
                self.pan = int(255 * 4 / 6 * min(1, pan))
                tilt = math.sqrt(x1 ** 2 + y1 ** 2)
                if tilt < 0.1:
                    tilt = 0
                else:
                    tilt = (tilt - 0.1) / (1 - 0.1)
                self.tilt = int((1 - min(1, tilt)) * 0.5 * 255)

            for fixture in fixtures:
                fixture.pan = self.pan
                fixture.tilt = self.tilt
                fixture.r = self.rgb[0]
                fixture.g = self.rgb[1]
                fixture.b = self.rgb[2]
                fixture.level = int(134)
                fixture.brightness = int(255)


class DualToneResponseFastSweep(Pattern):
    def __init__(self, state):
        self.state = state
        self.last_pulse = 0
        self.color = hsv_to_rgb(math.sin(time.time() * 5) * 0.5 + 0.5, 1, 1)
        self.colors = [hsv_to_rgb(random.random(), 1, 1), hsv_to_rgb(random.random(), 1, 1)]
        self.color_index = 0

    def update(self, fixtures):
        now = time.time()
        tempo = self.state.current_tempo

        if tempo > 0 and (self.state.beat or now - self.last_pulse > 60 / (tempo * 1)):
            self.last_pulse = now
            self.color = self.colors[self.color_index]
            self.color_index += 1
            if self.color_index >= len(self.colors):
                self.color_index = 0

        for fixture in fixtures:
            fixture.pan = int((math.sin(time.time() / 1) * 255 / 2 + 255 / 2))
            fixture.tilt = int((math.sin(time.time() / 1) * 255 / 2 + 255 / 2))
            fixture.r = int(255 * self.color[0])
            fixture.g = int(255 * self.color[1])
            fixture.b = int(255 * self.color[2])
            fixture.level = int(134)
            fixture.brightness = int(255)

        return False


class GrayResponseFastSweep(DualToneResponseFastSweep):
    def __init__(self, state):
        super().__init__(state)
        self.state = state
        self.last_pulse = 0
        self.color = hsv_to_rgb(math.sin(time.time() * 5) * 0.5 + 0.5, 1, 1)
        self.colors = [hsv_to_rgb(random.random(), 1, 1), hsv_to_rgb(random.random(), 1, 1)]
        self.color_index = 0

    def update(self, fixtures):
        now = time.time()
        tempo = self.state.current_tempo

        if tempo > 0 and (self.state.beat or now - self.last_pulse > 60 / (tempo * 1)):
            self.last_pulse = now
            self.color = self.colors[self.color_index]
            self.color_index += 1
            if self.color_index >= len(self.colors):
                self.color_index = 0

        for fixture in fixtures:
            fixture.pan = int((math.sin(time.time() / 1) * 255 / 2 + 255 / 2))
            fixture.tilt = int((math.sin(time.time() / 1) * 255 / 2 + 255 / 2))
            fixture.r = int(255 * self.color[0])
            fixture.g = int(255 * self.color[1])
            fixture.b = int(255 * self.color[2])
            fixture.level = int(134)
            fixture.brightness = int(255)

        return False


class RainbowSweep(Pattern):
    def __init__(self, state):
        self.state = state
        self.last_pulse = 0
        self.index = 0

    def update(self, fixtures):
        now = time.time()
        tempo = self.state.current_tempo

        if tempo > 0 and (self.state.beat or now - self.last_pulse > 60 / (tempo * 1)):
            self.last_pulse = now
            self.index += random.random() * 0.2 + 0.4

        color = hsv_to_rgb(math.sin(self.index) / 2 + 0.5, 1, 1)

        for fixture in fixtures:
            fixture.pan = int((math.sin(time.time() / 1) * 255 / 2 + 255 / 2))
            fixture.tilt = int((math.sin(time.time() / 1) * 255 / 2 + 255 / 2))
            fixture.r = int(255 * color[0])
            fixture.g = int(255 * color[1])
            fixture.b = int(255 * color[2])
            fixture.level = int(134)
            fixture.brightness = int(255)

        return False


class MellowSweep(Pattern):
    def __init__(self, state):
        self.state = state
        self.last_pulse = 0
        self.color = hsv_to_rgb(math.sin(time.time() * 5) * 0.5 + 0.5, 1, 1)
        self.colors = [hsv_to_rgb(random.random(), 1, 1), hsv_to_rgb(random.random(), 1, 1)]
        self.color_index = 0

    def update(self, fixtures):
        now = time.time()
        tempo = self.state.current_tempo

        if tempo > 0 and (self.state.beat or now - self.last_pulse > 60 / (tempo * 1)):
            self.last_pulse = now
            self.color = self.colors[self.color_index]
            self.color_index += 1
            if self.color_index >= len(self.colors):
                self.color_index = 0

        for fixture in fixtures:
            fixture.pan = int(time.time() * 25 % 255)
            fixture.tilt = 20
            fixture.r = int(255 * self.color[0])
            fixture.g = int(255 * self.color[1])
            fixture.b = int(255 * self.color[2])
            fixture.level = int(134)
            fixture.brightness = int(255)

        return False
