import random
import time
from colorsys import hsv_to_rgb

import math


class Pattern:
    def update(self, devices):
        return False


class DualToneResponseFastSweep(Pattern):
    def __init__(self, state):
        self.state = state
        self.last_pulse = 0
        self.color = hsv_to_rgb(math.sin(time.time() * 5) * 0.5 + 0.5, 1, 1)
        self.colors = [hsv_to_rgb(random.random(), 1, 1), hsv_to_rgb(random.random(), 1, 1)]
        self.color_index = 0

    def update(self, devices):
        now = time.time()
        tempo = self.state.current_tempo

        if tempo > 0 and (self.state.beat or now - self.last_pulse > 60 / (tempo * 1)):
            self.last_pulse = now
            self.color = self.colors[self.color_index]
            self.color_index += 1
            if self.color_index >= len(self.colors):
                self.color_index = 0

        for device in devices:
            device.pan = int((math.sin(time.time() / 1) * 255 / 2 + 255 / 2))
            device.tilt = int((math.sin(time.time() / 1) * 255 / 2 + 255 / 2))
            device.r = int(255 * self.color[0])
            device.g = int(255 * self.color[1])
            device.b = int(255 * self.color[2])
            device.level = int(134)
            device.brightness = int(255)

        return False


class RainbowSweep(Pattern):
    def __init__(self, state):
        self.state = state
        self.last_pulse = 0
        self.index = 0

    def update(self, devices):
        now = time.time()
        tempo = self.state.current_tempo

        if tempo > 0 and (self.state.beat or now - self.last_pulse > 60 / (tempo * 1)):
            self.last_pulse = now
            self.index += random.random() * 0.2 + 0.4

        color = hsv_to_rgb(math.sin(self.index) / 2 + 0.5, 1, 1)

        for device in devices:
            device.pan = int((math.sin(time.time() / 1) * 255 / 2 + 255 / 2))
            device.tilt = int((math.sin(time.time() / 1) * 255 / 2 + 255 / 2))
            device.r = int(255 * color[0])
            device.g = int(255 * color[1])
            device.b = int(255 * color[2])
            device.level = int(134)
            device.brightness = int(255)

        return False


class MellowSweep(Pattern):
    def __init__(self, state):
        self.state = state
        self.last_pulse = 0
        self.color = hsv_to_rgb(math.sin(time.time() * 5) * 0.5 + 0.5, 1, 1)
        self.colors = [hsv_to_rgb(random.random(), 1, 1), hsv_to_rgb(random.random(), 1, 1)]
        self.color_index = 0

    def update(self, devices):
        now = time.time()
        tempo = self.state.current_tempo

        if tempo > 0 and (self.state.beat or now - self.last_pulse > 60 / (tempo * 1)):
            self.last_pulse = now
            self.color = self.colors[self.color_index]
            self.color_index += 1
            if self.color_index >= len(self.colors):
                self.color_index = 0

        for device in devices:
            device.pan = int(time.time() * 25 % 255)
            device.tilt = 20
            device.r = int(255 * self.color[0])
            device.g = int(255 * self.color[1])
            device.b = int(255 * self.color[2])
            device.level = int(134)
            device.brightness = int(255)

        return False