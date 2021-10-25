"""
xled.pattern
~~~~~~~~~~~~

Author: Anders Holst (anders.holst@ri.se), 2021

This module contains a number of utility functions useful when creating
patterns, as well as several functions for creating various patterns.
The latter are meant primarily as a collection of examples. It should be
easy to construct many more types of patterns with just a few lines of code.

All the functions for creating patterns take a parameter ctr, which is a
HighControlInterface connected to the led lights on which the pattern will fit.
"""

from xled.ledcolor import hsl_color, rgb_color
import random
import math as m


# Some utility functions

def randomdiscrete(probs):
    """
    Takes a list of probabilities that should sum to one, and returns a random
    list index according to the probabilities in the list.
    """
    n = len(probs) - 1
    acc = 0.0
    ind = -1
    r = random.random()
    while acc <= r and ind < n:
        ind += 1
        acc += probs[ind]
    return ind


def randompoisson(lam):
    """
    Returns a random number from a Poisson distribution with parameter lam.
    """
    lp = 0.0
    k = -1
    while lp < lam:
        lp -= m.log(random.random())
        k += 1
    return k


def dimcolor(rgb, prop):
    """
    Dims a given rgb color to prop, which should be in the interval 0.0 - 1.0.
    """
    return tuple(map(lambda x: int(round(x * prop)), rgb))


def blendcolors(rgb1, rgb2, prop):
    """
    Blends two rgb colors so that prop comes from rgb2 and (1-prop) from rgb1,
    where prop should be a proportion in the interval 0.0 - 1.0.
    """
    return tuple(map(lambda c1, c2: int(round(c1 + (c2 - c1) * prop)), rgb1, rgb2))


def random_color():
    """
    Returns a random color drawn uniformly from the whole rgb-cube.
    """
    return rgb_color(random.random(), random.random(), random.random())


def random_hsl_color_func(hue=False, sat=False, light=False):
    """
    Returns a function that generates random colors within certain intervals.
    Each of the parameters hue, sat, and light can be either False, a constant,
    or an interval. If it is False (or not given at all), the parameter is
    randomized throughout its range, if it is an interval it is randomly drawn
    within this range, and if it is a constant it is set to that value.
    With this function you can thus construct a wide variety of random color
    generating functions.
    """

    def isnum(x):
        return type(x) in [float, int]

    def lightexp(y, x):
        return 1 - (1 - y)**x if y > 0 else (1 + y)**x - 1 if y < 0 else 0.0

    if not isnum(light):
        le = 1 + (1 if not isnum(sat) else 0) + (1 if not isnum(hue) else 0)
        if type(light) in [tuple, list]:
            l0 = lightexp(light[0], le)
            ld = lightexp(light[1], le) - l0
        else:
            l0 = -1.0
            ld = 2.0
    else:
        l0 = light
        ld = 0.0
    if not isnum(sat):
        se = 1 + (1 if not isnum(hue) else 0)
        if type(sat) in [tuple, list]:
            s0 = sat[0]**se
            sd = sat[1]**se - s0
        else:
            s0 = 0.0
            sd = 1.0
    else:
        s0 = sat
        sd = 0.0
    if not isnum(hue):
        if type(hue) in [tuple, list]:
            h0 = hue[0]
            hd = (hue[1] - hue[0]) % 1.0
        else:
            h0 = 0.0
            hd = 1.0
    else:
        h0 = hue
        hd = 0.0

    def func(*args):
        light = lightexp(l0 + random.random() * ld, 1.0 / le) if ld != 0.0 else l0
        sat = (s0 + random.random() * sd)**(1.0 / se) if sd != 0.0 else s0
        hue = (h0 + random.random() * hd) % 1.0 if hd != 0.0 else h0
        return hsl_color(hue, sat, light)

    return func


def sprinkle_pattern(ctr, pat, rgblst, freq):
    """
    Returns a copy of pat where a random number of pixels (with freq as
    expected number) are changed to a randomly picked color from rgblst.
    """
    pat = ctr.copy_pattern(pat)
    n = randompoisson(freq)
    inds = random.sample(range(ctr.num_leds), n)
    for i in inds:
        ctr.modify_pattern(pat, i, random.choice(rgblst))
    return pat


# Example functions for creating patterns

def make_alternating_color_pattern(ctr, rgblst):
    """
    Return a pattern of alternating colors from rgblst.
    """
    n = len(rgblst)
    return ctr.make_func_pattern(lambda i: rgblst[i % n])


def make_color_spectrum_pattern(ctr, offset=0, lightness=0.0):
    """
    Return a pattern of the color spectrum along the string.
    """
    return ctr.make_func_pattern(lambda i: hsl_color(((i - offset) / float(ctr.num_leds)) % 1.0, 1.0, lightness),
                                 circular=True)


def make_random_select_color_pattern(ctr, rgblst, prop=False):
    """
    Return a pattern of randomly selected colors from rgblst, optionally with
    the probabilities given by prop.
    """
    if prop and len(prop) == len(rgblst):
        return ctr.make_func_pattern(lambda i: rgblst[randomdiscrete(prop)])
    else:
        return ctr.make_func_pattern(lambda i: rgblst[random.randint(0, len(rgblst) - 1)])


def make_random_blend_color_pattern(ctr, rgb1, rgb2):
    """
    Return a pattern of random blends of the two given colors.
    """
    return ctr.make_func_pattern(lambda i: blendcolors(rgb1, rgb2, random.random()))


def make_random_colors_pattern(ctr, lightness=0.0):
    """
    Return a pattern of randomly drawn hues of the same lightness.
    """
    return ctr.make_func_pattern(lambda i: hsl_color(random.random(), 1.0, lightness))


def make_random_lightness_pattern(ctr, hue):
    """
    Return a pattern with the same hue but randomly drawn lightnesses.
    """
    return ctr.make_func_pattern(lambda i: hsl_color(hue, 1.0, random.random() * 2 - 1.0))


def make_random_hsl_pattern(ctr, hue=False, sat=False, light=False):
    """
    Return a pattern with random colors in the ranges specified by hue, sat, and light.
    """
    return ctr.make_func_pattern(random_hsl_color_func(hue, sat, light))
