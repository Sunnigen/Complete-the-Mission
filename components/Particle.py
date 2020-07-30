class ParticleSystem:
    # coordinates = None
    # particle_list = None

    def __init__(self):
        self.coordinates = []
        self.particle_list = []


class Particle:
    lifetime = 1
    x = 0
    y = 0
    fg = None
    bg = None
    char = None
    blink = None
    blink_duration = None
    propagate = False
    progagate_property = None

    def __init__(self, lifetime, fg=None, bg=None, char=None, blink=None, duration=None, forever=False, propagate=False,
                 propagate_property=None, particle_system=None):
        self.lifetime = lifetime
        self.fg = fg
        self.bg = bg
        self.char = char
        self.forever = forever
        self.propagate = propagate
        self.progagate_property = propagate_property
        self.particle_system = particle_system

    def update(self, dt):
        # Will cancel itself and not change self.lifetime if "self.forever" is True
        results = {}
        self.lifetime -= dt - (self.forever * dt)
        # print(self.lifetime)
        if self.lifetime <= 0:
            self.del_particle()

        results[self] = [self.propagate, self.progagate_property]

        return results

    def del_particle(self):
        # print('deleting particle')
        self.particle_system.particle_list.remove(self)

    def __repr__(self):
        return "Particle CurrentLifetime={} Pos=({}, {}) char={} fg={} bg={}".format(self.lifetime, self.x, self.y, self.char, self.fg, self.bg)