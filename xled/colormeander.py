"""
xled.colormeander
~~~~~~~~~~~~~~~~~

Author: Anders Holst (anders.holst@ri.se), 2021

Performing a random walk through color space

The idea with this module is to produce a sequence of slowly changing colors,
not just cycling through the spectrum in a deterministic and repetitive way,
but through the entire 3D color space, never repeating exactly the same path.

To use it, create a ColorMeander object (no mandatory arguments, but optional
ones described below). By default it starts at full white. By calling 'step'
it moves one step in color space. You can then retrieve the current color
coordinates by 'get()' (for rgb coordinates), 'get_hsl()' (for hsl coordinates),
'get_xyz()' (for the raw x,y,z-coordinates if you want to interpret them as a
color in some other way), or 'get_compl()' which gives the rgb coordinates of
the complementary color (opposite hue but same lightness and saturation).

It can be customized by a number of optional arguments when created:

'style' can be 'sphere' (the default, moves inside spherical color coordinates),
'cylinder' (to move inside cylindrical coordinates) or 'surface' (just moving on
the surface of the color sphere).

'speed' is the length to move inside the color space, should be much less than 1
for best effect, default is 0.01.

'noise' is the level of the random noise to add to the current direction. Should
also be less than 1 for best effect. Default is 0.15.

'start' is the starting point in space. Default is (0,0,1) which corresponds
to white. (0,0,-1) means black. (0,0,0) means mid gray. The initial direction
is random.
"""

from math import asin, atan2, sqrt, pi
import random

from xled.ledcolor import hsl_color


def hyp(*args):
    return sqrt(sum(map(lambda x: x * x, args)))


class ColorMeander():

    def __init__(self, style='sphere', speed=0.01, noise=0.15, start=(0.0, 0.0, 1.0)):
        self.steplen = speed
        self.noiselev = noise
        self.xyz = start
        self.dir = (random.random() - 0.5, random.random() - 0.5, random.random() - 0.5 - start[2])
        self.style = style

    def normalize(self, vec):
        nrm = hyp(*vec)
        if nrm == 0.0:
            nrm = 1.0
        return tuple(map(lambda v: v / nrm, vec))

    def xyz_to_hsl(self, x, y, z):
        if self.style == 'cylinder':
            h = atan2(y, x) / (2 * pi) + 0.5
            s = min(1.0, hyp(x, y))
            l = z
        else:
            h = atan2(y, x) / (2 * pi) + 0.5
            l = asin(z) * 2.0 / pi
            r = sqrt(x * x + y * y)
            r0 = sqrt(1 - z * z)
            s = min(1.0, r / r0 if r0 > 0.0 else 0.0)
        return (h, s, l)

    def xyz_color(self, x, y, z):
        return hsl_color(*self.xyz_to_hsl(x, y, z))

    def step(self):
        (nx, ny, nz) = tuple(map(lambda v, d: v + d * self.steplen, self.xyz, self.dir))
        if self.style == 'cylinder':
            if abs(nz) > 1.0:
                nz = max(-1.0, min(1.0, nz))
            nrm = hyp(nx, ny)
            if nrm > 1.0:
                nx = nx / nrm
                ny = ny / nrm
                self.dir = self.normalize((nx - self.xyz[0], ny - self.xyz[1], nz - self.xyz[2]))
            ndir = self.normalize(tuple(map(lambda v: v + random.random() * 2 * self.noiselev - self.noiselev, self.dir)))
            if abs(nz + ndir[2]) > 1.0:
                sgn = 1 if nz + ndir[2] > 0.0 else -1
                delta = sqrt(1.0 - (sgn - nz)**2)
                nrm = hyp(ndir[0], ndir[1])
                ndir = (ndir[0] * delta / nrm, ndir[1] * delta / nrm, sgn - nz)
        elif self.style == 'surface':
            nrm = hyp(nx, ny, nz)
            nx = nx / nrm
            ny = ny / nrm
            nz = nz / nrm
            ndir = self.normalize((nx - self.xyz[0], ny - self.xyz[1], nz - self.xyz[2]))
            ndir = self.normalize(tuple(map(lambda v: v + random.random() * 2 * self.noiselev - self.noiselev, ndir)))
        else:
            nrm = hyp(nx, ny, nz)
            if nrm > 1.0:
                nrm = nrm * nrm  # bounce equally much inside
                nx = nx / nrm
                ny = ny / nrm
                nz = nz / nrm
                self.dir = self.normalize((nx - self.xyz[0], ny - self.xyz[1], nz - self.xyz[2]))
            ndir = self.normalize(tuple(map(lambda v: v + random.random() * 2 * self.noiselev - self.noiselev, self.dir)))
        self.xyz = (nx, ny, nz)
        self.dir = ndir

    def get(self):
        return self.xyz_color(*self.xyz)

    def get_compl(self):
        return self.xyz_color(-self.xyz[0], -self.xyz[1], self.xyz[2])

    def get_xyz(self):
        return self.xyz

    def get_hsl(self):
        return self.xyz_to_hsl(*self.xyz)
