"""
xled.effects
~~~~~~~~~~~~

Author: Anders Holst (anders.holst@ri.se), 2021

A collection of moving effects created as subclasses of the Effect base class.
Mostly layout-independent effects, i.e with randomized positions, such as
glowing, breathing, and sparkling.
Most effects are highly configurable. Some specific examples of each effect
type are also provided.
"""

from xled.effect_base import Effect
from xled.colormeander import ColorMeander
from xled.pattern import blendcolors, randompoisson, random_hsl_color_func, sprinkle_pattern
from xled.ledcolor import hsl_color
import random


"""
Glowing effect

Similar to the Glow effect in the app, but seamless when it wraps around.
Check out the specific examples: Charcoal, Fire, Water, Aurora, Meadow.
"""


class Glowbit():

    def __init__(self, cols, bend, steps, initstep=False, loop=False):
        self.count = 0
        self.lastcol = (0, 0, 0)
        self.nextcol = (0, 0, 0)
        self.currcol = (0, 0, 0)
        self.loop = loop
        self.currind = initstep if initstep else steps
        self.steps = steps
        self.cols = cols
        self.bend = bend
        if self.loop:
            self.initcol1 = hsl_color(*self.cols[int((random.random()**self.bend) * len(self.cols))])
            self.initcol2 = hsl_color(*self.cols[int((random.random()**self.bend) * len(self.cols))])
            self.lastcol = self.initcol1
            self.nextcol = self.initcol2

    def getnext(self):
        if self.currind == self.steps:
            self.lastcol = self.nextcol
            if self.loop and self.count + self.steps >= self.loop:
                self.nextcol = self.initcol2
            elif self.loop and self.count + 2 * self.steps >= self.loop:
                self.nextcol = self.initcol1
            else:
                self.nextcol = hsl_color(*self.cols[int((random.random()**self.bend) * len(self.cols))])
            self.currind = 0
        self.currind += 1
        self.count += 1
        return blendcolors(self.lastcol, self.nextcol, float(self.currind) / self.steps)


class GlowEffect(Effect):

    def __init__(self, ctr, cols, bend, cycles, fps=False):
        super(GlowEffect, self).__init__(ctr)
        if fps:
            self.preferred_fps = fps
        self.cols = cols
        self.bend = bend
        self.cycles = cycles

    def reset(self, numframes):
        if type(self.cycles) == int:
            steps = [self.cycles]
        elif numframes:
            steps = []
            for n in range(self.cycles[0], self.cycles[-1] + 1):
                if numframes % n == 0:
                    steps.append(n)
            if not steps:
                steps = list(range(self.cycles[0], self.cycles[-1] + 1))
        else:
            steps = list(range(self.cycles[0], self.cycles[-1] + 1))
        pr1 = 13 if len(steps) % 13 != 0 else 7
        pr2 = 11 if len(steps) % 11 != 0 else 7
        self.glowarray = [Glowbit(self.cols, self.bend,
                                  steps[(i * pr1) % len(steps)],
                                  (i * pr2) % steps[(i * pr1) % len(steps)],
                                  numframes)
                          for i in range(self.ctr.num_leds)]

    def getnext(self):
        return self.ctr.make_func_pattern(lambda i: self.glowarray[i].getnext())


class Charcoal(GlowEffect):
    def __init__(self, ctr):
        cols = [[0.6057, 1.0, -0.99], [0.6171, 1.0, -0.8865], [0.6254, 1.0, -0.8083], [0.5796, 1.0, -0.7257], [0.6222, 1.0, -0.6779], [0.5606, 1.0, -0.6080], [0.5956, 1.0, -0.4838]]
        super(Charcoal, self).__init__(ctr, cols, 2, [2, 4], 8)


class Fire(GlowEffect):
    def __init__(self, ctr):
        cols = [[0.5689, 1.0, -0.2847], [0.5413, 1.0, -0.1809], [0.5119, 1.0, -0.0685], [0.6185, 1.0, -0.4416], [0.6206, 1.0, -0.6780], [0.5068, 1.0, 0.1797], [0.5603, 1.0, -0.0170], [0.45, 1.0, 0.1]]
        super(Fire, self).__init__(ctr, cols, 2, [3, 6], 20)


class Water(GlowEffect):
    def __init__(self, ctr):
        cols = [[0.0, 1.0, -0.2], [0.0, 1.0, -0.5], [0.05, 1.0, -0.3], [0.05, 1.0, 0.0], [0.1, 1.0, -0.5], [0.1, 1.0, 0.0], [0.15, 1.0, 0.0], [0.0, 1.0, 0.8]]
        super(Water, self).__init__(ctr, cols, 2, [3, 6], 20)


class Meadow(GlowEffect):
    def __init__(self, ctr):
        cols = [[0.2427, 1.0, -0.6294], [0.2556, 1.0, -0.3245], [0.2692, 1.0, -0.0834], [0.2456, 1.0, 0.0243], [0.2901, 1.0, 0.2506], [0.400, 1.0, 0.4219], [0.6065, 1.0, -0.1989], [0.7709, 1.0, -0.3420], [0.7833, 0.1259, 0.1001]]
        super(Meadow, self).__init__(ctr, cols, 2, [4, 8])


class Aurora(GlowEffect):
    def __init__(self, ctr):
        cols = [[0.0, 0.0, -0.8], [0.0, 0.0, -0.5], [0.0, 0.0, 0.0], [0.7401, 0.3679, 0.1246], [0.2744, 0.3180, 0.1759], [0.2789, 0.7024, 0.2672], [0.7435, 0.7191, 0.2302], [0.7483, 1.0, 0.1677], [0.1928, 1.0, -0.1506], [0.1, 1.0, 0.9]]
        super(Aurora, self).__init__(ctr, cols, 2, [6, 10])


class Brown(GlowEffect):
    def __init__(self, ctr):
        cols = [(0.5, 0.0, -1.0), (0.435, 1.0, -0.98), (0.477, 1.0, -0.96), (0.497, 1.0, -0.81), (0.45, 1.0, -0.765), (0.52, 1.0, -0.76)]
        super(Brown, self).__init__(ctr, cols, 3, [6, 10])


class GlowCP(GlowEffect):
    def __init__(self, ctr, cols):
        super(GlowCP, self).__init__(ctr, cols, 3, [4, 8])


"""
Sparkling effect

Similar to the Bright Twinkle effect in the app, but more versatile.
Again there are specific examples, but check out SparkleStars which has
varied color temperature of whites, unlike the origonal.
"""


class SparkleEffect(Effect):

    def __init__(self, ctr, freq, nfunc, sfunc, icol=(0, 0, 0)):
        super(SparkleEffect, self).__init__(ctr)
        self.freq = freq
        self.newfunc = nfunc
        self.stepfunc = sfunc
        self.initialcol = icol

    def reset(self, numframes):
        self.pattern = self.ctr.make_solid_pattern(self.initialcol)
        self.time = -1
        self.slist = []
        self.olist = list(range(0, self.ctr.num_leds))
        self.numframes = False  # intentionally set to False here
        if numframes:
            # walk a number of steps, count the sfunc cycle, and record the poisson outcomes
            self.blocktime = {}
            tmp = self.newfunc(0, 0)
            while self.stepfunc(0, tmp, self.time + 1, self.initialcol) is not False:
                self.getnext()
            self.leadintime = self.time
            self.leadin = [ele for ele in self.slist]
            self.numframes = numframes

    def getnext(self):
        self.time += 1
        if self.numframes:
            self.pattern = self.ctr.copy_pattern(self.pattern)  # only needed for movie
        if self.numframes and self.time >= self.numframes:
            for (ind, coldesc, tm) in self.leadin:
                if tm == self.time - self.numframes:
                    self.slist.append((ind, coldesc, self.time))
        else:
            if self.numframes and self.time >= self.numframes - self.leadintime:
                for (ind, coldesc, tm) in self.leadin:
                    if tm <= self.time - self.numframes + self.leadintime and ind in self.olist:
                        self.olist.remove(ind)
            n = randompoisson(self.freq)
            for j in range(n):
                if self.olist:
                    pos = random.randint(0, len(self.olist) - 1)
                    ind = self.olist[pos]
                    coldesc = self.newfunc(ind, self.time)
                    self.slist.append((ind, coldesc, self.time))
                    del self.olist[pos]
        remlst = []
        for pos, (ind, coldesc, stime) in enumerate(self.slist):
            col = self.stepfunc(ind, coldesc, self.time - stime, self.initialcol)
            if col is False:
                remlst.append(pos)
                self.olist.append(ind)
            elif col is True:
                remlst.append(pos)
                self.olist.append(ind)
                self.ctr.modify_pattern(self.pattern, ind, self.initialcol)
            else:
                self.ctr.modify_pattern(self.pattern, ind, col)
        for pos in reversed(sorted(remlst)):
            del self.slist[pos]
        return self.pattern


def randomhue(ind, tm):
    hue = random.random()
    return hue


def circularhuefunc(cycle):
    return lambda ind, tm: (tm / float(cycle)) % 1.0


def randomrgbfunc(hue=False, sat=False, light=False):
    func = random_hsl_color_func(hue, sat, light)
    return lambda ind, tm: func(0)


def randomwhitergb(ind, tm):
    r = random.random()
    return hsl_color(0.0 if r < 0.5 else 0.5, 1.0, 1.0 - abs(r - 0.5))


def selectedrgbfunc(cols):
    return lambda ind, tm : random.choice(cols)


def droplight(ind, hue, tm, initcol=False):
    if tm < 21:
        return hsl_color(hue, 1.0, 1.0 - tm / 10.0)
    elif tm == 21:
        return initcol or (0, 0, 0)
    else:
        return False


def pulselight(ind, hue, tm, initcol=False):
    if tm < 21:
        return hsl_color(hue, 1.0, -abs(tm - 10) / 10.0)
    elif tm == 21:
        return initcol or (0, 0, 0)
    else:
        return False


def looplight(ind, hue, tm, initcol=False):
    if tm < 25:
        return hsl_color(hue, 1.0, -1.0 + tm / 8.0) if tm < 16 else hsl_color(hue, 0.0, 1.0 - (tm - 16) / 4.0)
    elif tm == 25:
        return initcol or (0, 0, 0)
    else:
        return False


def revlooplight(ind, hue, tm, initcol=False):
    if tm < 25:
        return hsl_color(hue, 0.0, -1.0 + tm / 4.0) if tm < 8 else hsl_color(hue, 1.0, 1.0 - (tm - 8) / 8.0)
    elif tm == 25:
        return initcol or (0, 0, 0)
    else:
        return False


def flashlight_rgb(ind, rgb, tm, initcol=False):
    if tm == 0:
        return rgb
    elif tm == 1:
        return initcol or (0, 0, 0)
    else:
        return False


def flashlight_hue(ind, hue, tm, initcol=False):
    if tm == 0:
        return hsl_color(hue, 1.0, 0.0)
    elif tm == 1:
        return initcol or (0, 0, 0)
    else:
        return False


def flashcolor_rgb(ind, rgb, tm, initcol=False):
    if tm == 0:
        return hsl_color(0.0, 0.0, 1.0)
    elif tm < 6:
        return rgb
    elif tm < 12:
        return blendcolors(rgb, initcol or (0, 0, 0), (tm - 6) / 5.0)
    else:
        return False


def pulsecolor_rgb(ind, rgb, tm, initcol=False):
    if tm < 17:
        return blendcolors(rgb, initcol or (0, 0, 0), max(0.0, abs(tm - 8) / 8.0 - 0.0))
    else:
        return False


class SimpleStars(SparkleEffect):
    def __init__(self, ctr):
        super(SimpleStars, self).__init__(ctr, 8, randomhue, flashlight_hue)


class Pulselight(SparkleEffect):
    def __init__(self, ctr):
        super(Pulselight, self).__init__(ctr, 3, randomhue, pulselight)


class Looplight(SparkleEffect):
    def __init__(self, ctr, reverse=False):
        super(Looplight, self).__init__(ctr, 3, randomhue, looplight if not reverse else revlooplight)


class LooplightSpectrum(SparkleEffect):
    def __init__(self, ctr):
        super(LooplightSpectrum, self).__init__(ctr, 3, circularhuefunc(120), looplight)


class SparkleRandom(SparkleEffect):
    def __init__(self, ctr, hue=False, sat=False, light=False):
        super(SparkleRandom, self).__init__(ctr, 5, randomrgbfunc(hue, sat, light), pulsecolor_rgb)


class SparkleStars(SparkleEffect):
    def __init__(self, ctr):
        super(SparkleStars, self).__init__(ctr, 4, randomwhitergb, pulsecolor_rgb)


class SparkleCP(SparkleEffect):
    def __init__(self, ctr, cols):
        colsrgb = list(map(lambda hsl: hsl_color(*hsl), cols))
        super(SparkleCP, self).__init__(ctr, 5, selectedrgbfunc(colsrgb), pulsecolor_rgb)


"""
Breathing effect

Each led has a fixed color but slowly pulsing brightness.
"""


class Breathbit():

    def __init__(self, col, lspan, steps, initstep=False):
        self.currind = initstep if initstep else steps
        self.steps = steps
        self.hsteps = (steps - 1) / 2.0
        self.col1 = hsl_color(col[0], col[1], col[2])
        self.col2 = tuple(map(lambda x: int(round((1.0 - lspan) * x)), self.col1))
        self.preferred_fps = 6
        self.preferred_frames = 60

    def getnext(self):
        self.currind += 1
        if self.currind >= self.steps:
            self.currind = 0
        prop = abs(self.currind - self.hsteps) / self.hsteps
        return blendcolors(self.col1, self.col2, prop)


class BreathEffect(Effect):

    def __init__(self, ctr, cols, bend, lspan, cycles, fps=False):
        super(BreathEffect, self).__init__(ctr)
        if fps:
            self.preferred_fps = fps
        self.cols = cols
        self.bend = bend
        self.lspan = lspan
        self.cycles = cycles

    def reset(self, numframes):
        if type(self.cycles) == int:
            steps = [self.cycles]
        elif numframes:
            steps = []
            for n in range(self.cycles[0], self.cycles[-1] + 1):
                if numframes % n == 0:
                    steps.append(n)
            if not steps:
                steps = list(range(self.cycles[0], self.cycles[-1] + 1))
        else:
            steps = list(range(self.cycles[0], self.cycles[-1] + 1))
        pr1 = 13 if len(steps) % 13 != 0 else 7
        pr2 = 11 if len(steps) % 11 != 0 else 7
        colarray = [self.cols[int((random.random()**self.bend) * len(self.cols))]
                    for i in range(self.ctr.num_leds)]
        self.brarray = [Breathbit(colarray[i], self.lspan,
                                  steps[(i * pr1) % len(steps)],
                                  (i * pr2) % steps[(i * pr1) % len(steps)])
                        for i in range(self.ctr.num_leds)]

    def getnext(self):
        return self.ctr.make_func_pattern(lambda i: self.brarray[i].getnext())


class BreathCP(BreathEffect):
    def __init__(self, ctr, cols):
        super(BreathCP, self).__init__(ctr, cols, 1, 0.75, [12, 30])


"""
Glitter effect

Similar to the Sparkles effect in the app, of brigh flashing leds against a
solid background.
Specific examples are included in an attempt to mimic the "metallic luster"
effects of AWW leds: Gold, Silver, Bronze, RoseGold
"""


class GlitterEffect(Effect):

    def __init__(self, ctr, freq, cols, icol=(0, 0, 0)):
        super(GlitterEffect, self).__init__(ctr)
        self.freq = freq
        self.cols = list(map(lambda hsl: hsl_color(*hsl), cols))
        self.initialcol = hsl_color(*icol)
        self.preferred_fps = 10
        self.preferred_frames = 100

    def reset(self, numframes):
        self.pattern = self.ctr.make_solid_pattern(self.initialcol)

    def getnext(self):
        return sprinkle_pattern(self.ctr, self.pattern, self.cols, self.freq)


class Silver(GlitterEffect):
    def __init__(self, ctr):
        super(Silver, self).__init__(ctr, 10, [(0.0, 1.0, 0.8)], (0.0, 1.0, 0.3))


class Gold(GlitterEffect):
    def __init__(self, ctr):
        super(Gold, self).__init__(ctr, 10, [(0.5, 1.0, 0.8)], (0.5, 1.0, -0.2))


class RoseGold(GlitterEffect):
    def __init__(self, ctr):
        super(RoseGold, self).__init__(ctr, 10, [(0.57, 1.0, 0.8)], (0.57, 1.0, 0.05))


class Bronze(GlitterEffect):
    def __init__(self, ctr):
        super(Bronze, self).__init__(ctr, 10, [(0.58, 1.0, 0.5)], (0.58, 1.0, -0.4))


class StainlessSteel(GlitterEffect):
    def __init__(self, ctr):
        super(StainlessSteel, self).__init__(ctr, 10, [(0.0, 0.0, 1.0)], (0.0, 0.0, 0.0))


class GlitterCP(GlitterEffect):
    def __init__(self, ctr, cols):
        if len(cols) == 1:
            lcol = (cols[0][0], cols[0][1], min(1.0, cols[0][2] + 0.5))
            cols.append(lcol)
        super(Silver, self).__init__(ctr, 10, cols[1:], cols[0])


"""
Rotating pattern effect

Each led passes through a sequence by "rotating" the entire pattern.
Two scattered spectrum effects are included as examples, where each led
rapidly passes through the spectrum wheras the overall impression stays
constant.
"""


class RotateEffect(Effect):

    def __init__(self, ctr, pat, perm, step=1, speed=20):
        super(RotateEffect, self).__init__(ctr)
        self.origpattern = pat
        self.perm = perm
        self.step = step
        self.preferred_frames = ctr.num_leds // step
        self.preferred_fps = speed

    def reset(self, numframes):
        self.pattern = self.ctr.copy_pattern(self.origpattern)

    def getnext(self):
        currpattern = self.ctr.permute_pattern(self.pattern, self.perm, circular=True) if self.perm else self.pattern
        self.pattern = self.ctr.rotate_pattern(self.pattern, self.step, circular=True)
        return currpattern


class Spectrum(RotateEffect):
    def __init__(self, ctr, scattered=False, lightness=0.0, step=1):
        numleds = ctr.num_leds
        pat = ctr.make_func_pattern(lambda i: hsl_color(i / float(numleds), 1.0, lightness), circular=True)
        if scattered:
            perm = list(range(numleds))
            random.shuffle(perm)
        else:
            perm = False  # [i if i<numleds/2 else (numleds*3)//2 - 1 - i for i in range(numleds)]
        super(Spectrum, self).__init__(ctr, pat, perm, step=step)


class ScatteredSpectrum(Spectrum):
    def __init__(self, ctr):
        super(ScatteredSpectrum, self).__init__(ctr, True, 0.0)


class RotatingWhites(Spectrum):
    def __init__(self, ctr):
        super(RotatingWhites, self).__init__(ctr, True, 0.7, 5)


"""
Color meandering effect

Slowly and randomly changing color, such that whenever you look you will
never see it change, but whenever you look back after a while it has a
different color than last. Is not suitable for a movie, but requires
constant real time feeding, since it quickly consumes the available movie
capacity and never repeats exactly the same sequence of colors again.

Has a few different styles:
'solid' - all leds have the same color at every instance
'sequence' - the color changes propagate along the string
'scattered' - as sequence but with random permutation of the ordering of leds
'multi' - gives three random sequneces at once (every third led being the same color)
'tandem' - first half of string has one color and the second half the complement color
'blend' - two random sequences and each led has a color which is a random blend between them
"""


class ColorMeanderEffect(Effect):

    def __init__(self, ctr, style):
        super(ColorMeanderEffect, self).__init__(ctr)
        self.style = style  # solid, sequence, scattered, multi, blend, tandem, (whites?)
        self.pat = None
        self.cm = None
        self.updatefunc = None

    def reset(self, numframes):
        self.pat = self.ctr.make_func_pattern(lambda i: hsl_color(0, 0, 1))
        self.cm = ColorMeander()
        if self.style == 'solid':
            self.updatefunc = self.update_solid
        elif self.style == 'sequence':
            self.updatefunc = self.update_sequence
        elif self.style == 'scattered':
            self.updatefunc = self.update_scattered
            self.perm = list(range(self.ctr.num_leds))
            random.shuffle(self.perm)
            self.pat0 = self.pat
        elif self.style == 'tandem':
            self.updatefunc = self.update_tandem
        elif self.style == 'multi':
            self.cms = [ColorMeander() for i in range(3)]
            self.updatefunc = self.update_multi
        elif self.style == 'blend':
            self.cm2 = ColorMeander()
            self.props = [random.random() for i in range(self.ctr.num_leds)]
            self.updatefunc = self.update_blend
        else:
            print("Bad Meander style")
            self.update_func = lambda : None

    def update_solid(self):
        self.cm.step()
        self.pat = self.ctr.make_func_pattern(lambda i: self.cm.get())

    def update_sequence(self):
        self.cm.step()
        self.pat = self.ctr.shift_pattern(self.pat, 1, self.cm.get(), circular=True)

    def update_scattered(self):
        self.cm.step()
        self.pat0 = self.ctr.shift_pattern(self.pat0, 1, self.cm.get())
        self.pat = self.ctr.permute_pattern(self.pat0, self.perm)

    def update_tandem(self):
        self.cm.step()
        (h, s, l) = self.cm.get_hsl()
        col1 = hsl_color(h, s, l)
        col2 = hsl_color((h + 0.5) % 1.0, s, l)
        self.pat = self.ctr.make_func_pattern(lambda i: col1 if i < self.ctr.num_leds // 2 else col2)

    def update_multi(self):
        for cm in self.cms:
            cm.step()
        self.pat = self.ctr.make_func_pattern(lambda i: self.cms[i % len(self.cms)].get())

    def update_blend(self):
        self.cm.step()
        self.cm2.step()
        self.pat = self.ctr.make_func_pattern(lambda i: blendcolors(self.cm.get(), self.cm2.get(), self.props[i]))

    def getnext(self):
        self.updatefunc()
        return self.pat
