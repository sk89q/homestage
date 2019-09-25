class Fixture:
    mapping = []

    def __new__(cls, address):
        o = super().__new__(cls)
        for key in o.mapping:
            if not hasattr(o, key):
                setattr(o, key, 0)
        o.address = address
        return o

    @property
    def values(self):
        return [getattr(self, k) for k in self.mapping]


class MovingHeadLight(Fixture):
    mapping = ['pan', 'pan_fine', 'tilt', 'tilt_fine', 'move_speed', 'level', 'r', 'g', 'b', 'w', 'color_preset',
               'color_cycle_speed', 'control', 'reset']
    level = 134


class LEDWash(Fixture):
    mapping = ['brightness', 'r', 'g', 'b', 'strobe', 'control', 'speed']


class MiniSpider(Fixture):
    mapping = ['motor1', 'motor2', 'dimmer', 'strobe', 'led1', 'led2', 'led3', 'led4', 'led5', 'led6', 'led7', 'led8',
               'macro', 'speed', 'reset']
    dimmer = 255

    @property
    def r(self):
        return self.led1

    @r.setter
    def r(self, value):
        self.led1 = self.led5 = value

    @property
    def g(self):
        return self.led2

    @g.setter
    def g(self, value):
        self.led2 = self.led6 = value

    @property
    def b(self):
        return self.led1

    @b.setter
    def b(self, value):
        self.led3 = self.led7 = value
