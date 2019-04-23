class DMXDevice:
    mapping = []

    def __new__(cls):
        o = super().__new__(cls)
        for key in o.mapping:
            if not hasattr(o, key):
                setattr(o, key, 0)
        return o

    @property
    def values(self):
        return [getattr(self, k) for k in self.mapping]


class MovingHeadLight(DMXDevice):
    mapping = ['pan', 'pan_fine', 'tilt', 'tilt_fine', 'move_speed', 'level', 'r', 'g', 'b', 'w', 'color_preset',
               'color_cycle_speed', 'control', 'reset']
    level = 134


class LEDWash(DMXDevice):
    mapping = ['brightness', 'r', 'g', 'b', 'strobe', 'control', 'speed']
