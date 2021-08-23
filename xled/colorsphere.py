
"""
xled.colorsphere
~~~~~~~~~~~~~~~~

Author: Anders Holst (anders.holst@ri.se), 2021

This module implements an interactive 3-dimensional color picker -
to the author's knowledge the first ever 3-dimensional color picker.
It can be connected directly to controlling the led lights by a
suitable callback function. One simple example callback function is
provided.

The main entrypoint is the class ColorPicker, which takes a callback
function to call whenever a color is picked, and an optional boolean
argument useevent telling whether the callback wishes to have the
button press event for picking in addition to the hsl-coordinates
of the picked color.

There is also an entrypoint launch_colorpicker, which takes a
HighControlInterface object connected to some led lights as argument,
and then shows a window with the color sphere. When the user picks a
color in the sphere, it sets the color of the lights accordingly.

The color sphere represents the whole color body, where one pole
is black, the other pole is white, and the color circle is around the
equator. If you follow a meridian from the black pole, the color will
gradually increase in strength to its maximum brilliance and then
seamlessly continue to become brighter all the way to white. Less
saturated colors are inside the sphere. The axis through the middle of
the sphere between the poles contains all grays from black to
white. Thus, the hue is represented by the longitude, the lightness by
the latitude, and the saturation by the proportion from the surface to
the center black-white axis of the sphere. You can rotate the sphere
either by dragging the surface, or using the scroll wheel. Shift-
scrolling goes sideways. Control scrolling goes inside the spere.

The module requires matplotlib and numpy, and a fairly fast computer to
run.
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from math import floor, sqrt, sin, cos, atan2, acos, pi
import random

from xled.ledcolor import get_color_style, hsl_color
from xled.windowmgr import WindowMgr


brightness = [0.25, 0.54, 0.21]
ramp_n = {}
ramp_v = {}
ramp_d = {}
ramp = {}
ramp["3col"] = [[0.0, 0.0, 1.0], [0.0, 0.5, 0.5], [0.0, 1.0, 0.0], [0.5, 0.5, 0.0], [1.0, 0.0, 0.0], [0.5, 0.0, 0.5], [0.0, 0.0, 1.0]]
ramp["4col"] = [[0.0, 0.0, 1.0], [0.0, 0.5, 0.5], [0.0, 1.0, 0.0], [0.25, 0.75, 0.0], [0.5, 0.5, 0.0], [0.75, 0.25, 0.0], [1.0, 0.0, 0.0], [0.5, 0.0, 0.5], [0.0, 0.0, 1.0]]
ramp["6col"] = [[0.0, 0.0, 1.0], [0.0, 0.5, 0.5], [0.0, 1.0, 0.0], [0.25, 0.75, 0.0], [0.5, 0.5, 0.0], [0.625, 0.375, 0.0], [0.75, 0.25, 0.0], [0.875, 0.125, 0.0], [1.0, 0.0, 0.0], [0.5, 0.0, 0.5], [1.0 / 3, 0.0, 2.0 / 3], [1.0 / 6, 0.0, 5.0 / 6], [0.0, 0.0, 1.0]]
ramp["8col"] = [[0.0, 0.0, 1.0], [0.0, 0.5, 0.5], [0.0, 1.0, 0.0], [0.5, 0.5, 0.0], [0.75, 0.25, 0.0], [1.0, 0.0, 0.0], [0.5, 0.0, 0.5], [0.25, 0.0, 0.75], [0.0, 0.0, 1.0]]
ramp["10col"] = [[0.0, 0.0, 1.0], [0.0, 0.25, 0.75], [0.0, 0.5, 0.5], [0.0, 1.0, 0.0], [0.5, 0.5, 0.0], [4.0 / 6, 2.0 / 6, 0.0], [5.0 / 6, 1.0 / 6, 0.0], [1.0, 0.0, 0.0], [0.5, 0.0, 0.5], [0.25, 0.0, 0.75], [0.0, 0.0, 1.0]]
for key in ramp:
    ramp_n[key] = len(ramp[key]) - 1
    ramp_v[key] = np.array(list(map(lambda x: x + [max(x)], ramp[key]))).transpose()
    ramp_d[key] = np.array(list(map(lambda v: np.append(v[1:], v[-1]) - v, ramp_v[key])))
xxarr = np.array([i for j in range(101) for i in range(101)])
yyarr = np.array([j for j in range(101) for i in range(101)])


def hsl_color_im(h, s, l):
    tmp = h * ramp_n[get_color_style()[0]]
    hind = int(floor(tmp))
    hprop = tmp % 1.0
    rgbm = tuple(map(lambda v, d: v[hind] + d[hind] * hprop,
                     ramp_v[get_color_style()[0]],
                     ramp_d[get_color_style()[0]]))
    rgb = tuple(map(lambda x: x / rgbm[3], rgbm[0:3]))
    ll = (l + 1.0) * 0.5
    if get_color_style()[1] == "linear":
        if ll < 0.5:
            t1 = l + 1.0
            t2 = 0.0
        else:
            t1 = 1.0 - l
            t2 = l
    else:
        br = sum(map(lambda c, b: c * b, rgb, brightness))
        p = min(1.0, (1.0 - ll) / (1.0 - br), (1.0 - ll) / (1.0 - brightness[1]))
        t1 = ll * p / ((br - 1.0) * p + 1.0)
        t2 = max(0.0, ll - t1 * br)
    t1 = s * t1
    t2 = s * t2 + ll * (1.0 - s)
    return tuple(map(lambda c: pow(max(0.0, min(1.0, c * t1 + t2)), 0.417), rgb))


def rotxmatrix(ang):
    sa = sin(ang)
    ca = cos(ang)
    return np.matrix([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]])


def rotymatrix(ang):
    sa = sin(ang)
    ca = cos(ang)
    return np.matrix([[1, 0, 0], [0, ca, sa], [0, -sa, ca]])


def origmatrix():
    return np.matrix([[1, 0, 0], [0, 0, -1], [0, 1, 0]])


class ColorSphere():

    def __init__(self, fig, rect, wdt, hgt, callback, useevent=False):
        self.callback = callback
        self.useevent = useevent
        self.mouse_color_callback = None
        self.lastbpos = False
        self.p1 = False
        self.fig = fig
        self.xoff = wdt * rect[0]
        self.yoff = hgt * rect[1]
        self.size = min(wdt * rect[2], hgt * rect[3])
        self.diam = 1.0
        cent = (0, 0)
        self.ax = fig.add_axes(rect, frame_on=False, xticks=[], yticks=[])
        self.gray1 = hsl_color_im(0.0, 0.0, 0.0)
        self.gray2 = hsl_color_im(0.0, 0.0, 0.5)
        self.im = self.ax.imshow([[self.gray1]], origin='lower')
        diameps = 0.5 * 10 / self.size
        self.circ2 = mpl.patches.Ellipse(cent, self.diam, self.diam,
                                         linewidth=0, edgecolor=self.gray2, fill=False)
        self.circ1 = mpl.patches.Ellipse(cent, self.diam + diameps, self.diam + diameps,
                                         linewidth=10 * 0.75, edgecolor=self.gray1, fill=False)
        self.ax.add_artist(self.circ2)
        self.ax.add_artist(self.circ1)
        self.rad = 1.0
        self.dotsz = self.size / 100.0
        self.eye = origmatrix()
        self.draw()

    def coordinates(self, xx, yy):
        x = xx / (self.size * 0.5) - 1.0
        y = yy / (self.size * 0.5) - 1.0
        p2 = x * x + y * y
        r2 = self.rad * self.rad
        if p2 > r2 + 2.0 * self.rad * self.dotsz / (self.size * 0.5):
            return False
        z = sqrt(max(0.0, r2 - p2))
        pe = list(map(lambda v: v[0], self.eye * [[x], [y], [z]]))
        h = (atan2(pe[0], pe[1]) / (2 * pi)) % 1.0
        if self.rad < 1.0:
            q1 = pe[0] * pe[0] + pe[1] * pe[1]
            q2 = max(0.0, 1.0 - pe[2] * pe[2])
            s = sqrt(q1 / q2) if q2 > q1 else 1.0
        else:
            s = 1.0
        l = 1.0 - 2.0 * acos(max(-1.0, min(1.0, pe[2]))) / pi
        return (h, s, l)

    def draw1(self, event=None):
        ndiam = self.diam * (0.5 + self.rad / 2.0)
        self.circ2.width = ndiam
        self.circ2.height = ndiam
        self.circ2.set_linewidth((1.0 - ndiam / self.diam) * self.size * 0.75)
        arr = [[hsl_color_im(*(self.coordinates(self.dotsz * i, self.dotsz * j) or (0, 0, 0)))
                for i in range(101)]
               for j in range(101)]
        if event and self.mouse_color_callback:
            xind = int((event.x - self.xoff) // self.dotsz)
            yind = int((event.y - self.yoff) // self.dotsz)
            if (xind - 50.5)**2 + (yind - 50.5)**2 <= 50.5**2:
                self.mouse_color_callback(arr[yind][xind], redraw=False)
        self.im.set_array(arr)

    def draw(self, event=None):
        ndiam = self.diam * (0.5 + self.rad / 2.0)
        self.circ2.width = ndiam
        self.circ2.height = ndiam
        self.circ2.set_linewidth((1.0 - ndiam / self.diam) * self.size * 0.75)
        arr = self.coordinates_color_array(xxarr * self.dotsz, yyarr * self.dotsz)
        arr = np.array(arr).reshape((101, 101, 3))
        if event and self.mouse_color_callback:
            xind = int((event.x - self.xoff) // self.dotsz)
            yind = int((event.y - self.yoff) // self.dotsz)
            if (xind - 50.5)**2 + (yind - 50.5)**2 <= 50.5**2:
                self.mouse_color_callback(arr[yind][xind], redraw=False)
        self.im.set_array(arr)

    def scroll_event(self, event):
        changed = False
        if event.key == "control":
            if event.button == "up":
                if self.rad < 1.0:
                    self.rad = min(1.0, self.rad + 0.01)
                    changed = True
            elif event.button == "down":
                if self.rad > 0.01:
                    self.rad = max(0.01, self.rad - 0.01)
                    changed = True
        elif event.key == "shift":
            if event.button == "up":
                self.eye = self.eye * rotxmatrix(-5.0 * pi / 180.0)
                changed = True
            elif event.button == "down":
                self.eye = self.eye * rotxmatrix(5.0 * pi / 180.0)
                changed = True
        else:
            if event.button == "up":
                self.eye = self.eye * rotymatrix(-5.0 * pi / 180.0)
                changed = True
            elif event.button == "down":
                self.eye = self.eye * rotymatrix(5.0 * pi / 180.0)
                changed = True
        if changed:
            self.draw(event)

    def button_press_event(self, event):
        self.lastbpos = (event.x, event.y)
        self.starteye = self.eye
        x = (event.x - self.xoff) / (self.size * 0.5) - 1.0
        y = (event.y - self.yoff) / (self.size * 0.5) - 1.0
        rr2 = x * x + y * y
        r2 = self.rad * self.rad
        if rr2 <= r2 + 2.0 * self.rad * self.dotsz / (self.size * 0.5):
            self.p1 = np.array([x, y, sqrt(max(0.0, r2 - rr2))])
        else:
            self.p1 = False

    def button_release_event(self, event):
        if self.lastbpos == (event.x, event.y):
            if event.button == 1 and self.callback:
                coord = self.coordinates(event.x - self.xoff, event.y - self.yoff)
                if coord:
                    if self.useevent:
                        self.callback(coord, event)
                    else:
                        self.callback(coord)

    def motion_notify_event(self, event):
        if self.p1 is not False:
            x = (event.x - self.xoff) / (self.size * 0.5) - 1.0
            y = (event.y - self.yoff) / (self.size * 0.5) - 1.0
            p2 = np.array([x, y, sqrt(max(0.0, self.rad * self.rad - x * x - y * y))])
            p1 = self.p1
            q = np.cross(p1, p2)
            l = np.vdot(q, q)
            if l == 0.0:
                self.eye = self.starteye
            else:
                q = q / sqrt(l)
                a = atan2(-q[1], q[2])
                b = atan2(sqrt(q[1] * q[1] + q[2] * q[2]), q[0])
                v = atan2(np.vdot(np.cross(q, p1), p2), np.vdot(p1, p2))
                tt = rotxmatrix(b) * rotymatrix(a)
                self.eye = self.starteye * tt.transpose() * rotymatrix(v) * tt
            self.draw()

    def color_change_event(self, event):
        hsl = self.coordinates(event.x - self.xoff, event.y - self.yoff)
        if hsl and self.mouse_color_callback:
            self.mouse_color_callback(hsl_color_im(*hsl))

    def key_press_event(self, event):
        pass

    def coordinates_color_array(self, xxarr, yyarr):
        x = xxarr / (self.size * 0.5) - 1.0
        y = yyarr / (self.size * 0.5) - 1.0
        p2 = x * x + y * y
        r2 = self.rad * self.rad
        z = np.sqrt((r2 - p2 + np.abs(r2 - p2)) / 2.0)
        mask = (p2 < r2 + 2.0 * self.rad * self.dotsz / (self.size * 0.5)).astype(int)
        x = np.multiply(x, mask)
        y = np.multiply(y, mask)
        z = np.multiply(z, mask)
        pe = self.eye * [x, y, z]
        pe = (pe + 1.0 - np.abs(pe - 1.0)) / 2.0
        pe = (pe - 1.0 + np.abs(pe + 1.0)) / 2.0
        h = (np.arctan2(pe[0], pe[1]) / (2 * pi)) % 1.0
        if self.rad < 1.0:
            qe = np.multiply(pe, pe)
            q1 = qe[0] + qe[1]
            q2 = 1.0001 - qe[2]
            s = np.sqrt(q1 / q2)
            s = (s + 1.0 - np.abs(s - 1.0)) / 2.0
        else:
            s = np.multiply(np.ones(pe[2].shape), mask)
        l = 1.0 - 2.0 * np.arccos(pe[2]) / pi
        tmp = h * ramp_n[get_color_style()[0]]
        hind = np.floor(np.array(tmp)[0]).astype(int)
        hprop = tmp % 1.0
        v = np.take_along_axis(ramp_v[get_color_style()[0]], np.array([hind] * 4), 1)
        d = np.take_along_axis(ramp_d[get_color_style()[0]], np.array([hind] * 4), 1)
        rgbm = np.array(v + np.multiply(d, hprop))
        rgb = np.divide(np.matrix(rgbm[0:3]), rgbm[3])
        ll = (l + 1.0) * 0.5
        if get_color_style()[1] == "linear":
            t1 = 1.0 - np.abs(l)
            t2 = (l + 1.0 - t1) * 0.5
        else:
            br = brightness * rgb
            lmin = (ll + br - np.abs(ll - br)) / 2.0
            lmin = (lmin + brightness[1] - np.abs(lmin - brightness[1])) / 2.0
            p = (1.0 - ll) / (1.0 - lmin)
            t1 = np.multiply(ll, p) / (np.multiply(br - 1.0, p) + 1.0)
            t2 = ll - np.multiply(t1, br)
        t1 = np.multiply(s, t1)
        t2 = np.multiply(s, t2) + np.multiply(ll, 1.0 - s)
        rgb = np.add(np.multiply(rgb, t1), t2)
        rgb = (rgb + 1.0 - np.abs(rgb - 1.0)) / 2.0
        rgb = (rgb + np.abs(rgb)) / 2.0
        rgb = np.power(rgb, 0.417)
        return rgb.transpose()


class ColorSample():

    def __init__(self, fig, rect, bw, initcol):
        self.fig = fig
        self.ax = fig.add_axes(rect, frame_on=False, xticks=[], yticks=[])
        self.rect = rect
        self.sqr = plt.Rectangle((0, 0), 1.0, 1.0,
                                 linewidth=bw * 0.75, edgecolor=(0, 0, 0), facecolor=initcol)
        self.ax.add_artist(self.sqr)

    def set_color(self, rgb, redraw=True):
        self.sqr.set_facecolor(rgb)
        if redraw:
            self.fig.canvas.draw()


class ColorPicker():

    def __init__(self, callback, useevent=False):
        width = 500
        height = 500
        rect = (0.1, 0.1, 0.8, 0.8)
        self.win = WindowMgr("xled color picker", width, height, 1, 1)
        self.win.set_background(hsl_color_im(0.0, 0.0, 0.0))
        self.sphere = ColorSphere(self.win.fig, rect, width, height, callback, useevent)
        self.sample = ColorSample(self.win.fig, (0.04, 0.04, 0.16, 0.16), 2, hsl_color_im(0.0, 0.0, 1.0))
        self.win.register_target(rect, self.sphere)
        self.win.set_motion_callback(self.sphere.color_change_event)
        self.sphere.mouse_color_callback = self.sample.set_color


# An example application of the color picker. Call launch_colorpicker with the
# HighControlInterface as argument. Click on a color to select it. Shift-click
# to select several colors. Control-click to blend the last two colors.

def blendcols(rgb1, rgb2, p):
    return tuple(map(lambda c1, c2: int(round(c1 + (c2 - c1) * p)), rgb1, rgb2))


def callbackfunc(ctr):
    lasthsl = [False]

    def domessage(hsl, event):
        if event.key == "control" and lasthsl[0] is not False:
            del lasthsl[:-1]
            col1 = hsl_color(*lasthsl[0])
            col2 = hsl_color(*hsl)
            lasthsl[0] = hsl
            pat = ctr.make_func_pattern(lambda i: blendcols(col1, col2, random.random()))
        elif event.key == "shift" and lasthsl[0] is not False:
            lasthsl.append(hsl)
            cols = list(map(lambda hsl: hsl_color(*hsl), lasthsl))
            n = len(cols)
            pat = ctr.make_func_pattern(lambda i: cols[i % n])
        else:
            col = hsl_color(*hsl)
            del lasthsl[1:]
            lasthsl[0] = hsl
            pat = ctr.make_func_pattern(lambda i: col)
        ctr.show_pattern(pat)
    return domessage


global_cp = False


def launch_colorpicker(ctr):
    global global_cp
    global_cp = ColorPicker(callbackfunc(ctr), useevent=True)
