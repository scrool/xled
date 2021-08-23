
"""
xled.ledcolor
~~~~~~~~~~~~~

Author: Anders Holst (anders.holst@ri.se), 2021

This module provides a color model adapted for the led lights.
It is based on HSL (Hue - Saturation - Lightness).

The main entry-point is hsl_color(h, s, l) which takes values for hue,
saturation and lightness, and returns a tuple of rgb values.
Hue is in the range 0.0 - 1.0 (where both ends represent blue).
Saturation is also in the range 0.0 - 1.0.
Lighness however is in the range -1.0 - +1.0, where -1.0 is black, +1.0
is white, and 0.0 represents the maximum chroma of the hue.

You can choose between 4 color circles and two lightness policies, with the
function set_color_style which understands the following tags:
"3col": Standard R-G-B color circle with the colors Blue-Cyan-Green-
        -Yelow-Red-Magenta at equal distances.
"4col": NCS-color circle with Blue-Green-Yellow-Red at equal distances.
        Not particularly useful here but included if someone prefers it.
"6col": The common paintbox color circle with Blue-Green-Yellow-Orange-
        -Red-Purple at equal distances
"8col": A combined color circle, with Blue-Cyan-Green-Yellow-Orange-Red-
        -Magenta-Purple at equal distances. This is the most "perceptually
        even" circle, and in addition happens to have complementary colors
        placed opposite to each other.
"linear": A traditional lightness policy, where the light increases
          linearly for each hue from black (-1) up to maximum chroma (0)
          and then linearly from there to white (1). However, different
          hues have then different lightness with this policy.
"equilight": A lightness policy enforcing that all hues at a given
             lightness have the same perceived brightness. Maximum
             chroma occurs at different lightness for different hues.
A standard HSL color model would have "3col" and "linear", whereas the
default setting here is "8col" and "equilight" because it is more intuitive
and easier to work with.

The RGB type led lights are originally not well white balanced. They
have a cold purplish tinge when fully lit. The provided color model
compensates for this by balancing the lights. With this model you
can easily select any white you want - neutral, warm, cold, pinkish
or greenish - without the need to go to RGBW.
"""

led_gamma = 1.0

led_brightness = [0.35, 0.50, 0.15]

led_balance = [0.9, 1.0, 0.6]

col_styles_dict = {"3col": [0.0, 1.0 / 6.0, 2.0 / 6.0, 3.0 / 6.0, 4.0 / 6.0, 5.0 / 6.0, 1.0],
                   "4col": [0.0, 1.0 / 8.0, 1.0 / 4.0, 2.0 / 4.0, 3.0 / 4.0, 7.0 / 8.0, 1.0],
                   "6col": [0.0, 1.0 / 12.0, 1.0 / 6.0, 1.0 / 3.0, 2.0 / 3.0, 3.0 / 4.0, 1.0],
                   "8col": [0.0, 1.0 / 8.0, 2.0 / 8.0, 3.0 / 8.0, 5.0 / 8.0, 6.0 / 8.0, 1.0],
                   "10col": [0.0, 2.0 / 10.0, 3.0 / 10.0, 4.0 / 10.0, 7.0 / 10.0, 8.0 / 10.0, 1.0]}

col_style = ("8col", "equilight")


# Internal functions

def colorgamma(x):
    global led_gamma
    return x if led_gamma == 1.0 else pow(x, led_gamma)


def invcolorgamma(x):
    global led_gamma
    return x if led_gamma == 1.0 else pow(x, 1.0 / led_gamma)


def colorgamma_image(x):
    return (pow(x, 1.0 / 2.4) * 1.055 - 0.055) if x > 0.0031308 else x * 12.92


def invcolorgamma_image(x):
    return pow((x + 0.055) / 1.055, 2.4) if x > 0.04045 else x / 12.92


def color_brightness(r, g, b):
    return sum(map(lambda c, br: c * br, [r, g, b], led_brightness))


# Entry points

def set_color_style(style):
    """
    Set the color circle and lightness policy to use in the color model.
    Possible color circles are: "3col", "4col", "6col" and "8col".
    Possible lightness policies are: "linear" and "equilight".

    :param str style: color circle or lightness policy to use.
    :rtype: tuple
    """
    global col_style, col_styles_dict
    if style in ["linear", "equilight"]:
        col_style = (col_style[0], style)
        return col_style
    elif style in col_styles_dict:
        col_style = (style, col_style[1])
        return col_style
    else:
        return False


def get_color_style():
    """
    Return the currently used color circle and lightness policy as a tuple.

    :rtype: tuple
    """
    global col_style
    return col_style


def rgb_color(r, g, b):
    """
    Takes r, g and b values in the range 0.0 - 1.0, and converts it to an
    rgb tuple in the range 0-255, adjusted for white balance of the leds.

    :param float r: red component (0.0 - 1.0)
    :param float g: green component (0.0 - 1.0)
    :param float b: blue component (0.0 - 1.0)
    :rtype: tuple
    """
    global led_balance
    return tuple(map(lambda c, b: max(0, min(255, int(255 * b * colorgamma(c)))),
                     [r, g, b], led_balance))


def image_to_led_rgb(r, g, b):
    """
    Converts rgb values for a computer image pixel into rgb values for a led,
    compensating for gamma correction in the image.
    The input values and the returned rgb values are all in the range 0-255.

    :param float r: red component (0 - 255)
    :param float g: green component (0 - 255)
    :param float b: blue component (0 - 255)
    :rtype: tuple
    """
    return tuple(map(lambda c, bal: max(0, min(255, int(255 * bal * colorgamma(invcolorgamma_image(c / 255.0))))),
                     [r, g, b], led_balance))


def led_to_image_rgb(r, g, b):
    """
    Converts rgb values for a led into rbg values for a computer image pixel,
    compensating for gamma correction in the image.
    The input values and the returned rgb values are all in the range 0-255.

    :param float r: red component (0 - 255)
    :param float g: green component (0 - 255)
    :param float b: blue component (0 - 255)
    :rtype: tuple
    """
    return tuple(map(lambda c, bal: max(0, min(255, int(255 * colorgamma_image(invcolorgamma(c / (bal * 255.0)))))),
                     [r, g, b], led_balance))


def hsl_color(h, s, l):
    """
    Takes hue (0.0 - 1.0), saturation (0.0 - 1.0), and lightness (-1.0 - 1.0)
    values and converts it to an rgb tuple in the range 0-255.

    :param float h: hue component (0.0 - 1.0)
    :param float s: saturation component (0.0 - 1.0)
    :param float l: lightness component (-1.0 - 1.0)
    :rtype: tuple
    """
    global col_style, col_styles_dict
    hramp = col_styles_dict[col_style[0]]
    ir = 1.0 / led_balance[0]
    ig = 1.0 / led_balance[1]
    ib = 1.0 / led_balance[2]
    irg = min(ir, ig)
    irb = min(ir, ib)
    igb = min(ig, ib)
    iramp = [(0, 0, ib), (0, igb / 2, igb / 2), (0, ig, 0), (irg / 2, irg / 2, 0), (ir, 0, 0), (irb / 2, 0, irb / 2), (0, 0, ib)]
    i = 0
    while h > hramp[i + 1]:
        i += 1
    p = (h - hramp[i]) / (hramp[i + 1] - hramp[i])
    (r, g, b) = tuple(map(lambda x1, x2: p * (x2 - x1) + x1, iramp[i], iramp[i + 1]))
    nrm = max(r / ir, g / ig, b / ib)
    (r, g, b) = tuple(map(lambda x: x / nrm, (r, g, b)))
    ll = (l + 1.0) * 0.5
    if col_style[1] == "linear":
        if ll < 0.5:
            t1 = l + 1.0
            t2 = 0.0
        else:
            t1 = 1.0 - l
            t2 = l
    else:
        br = color_brightness(r, g, b)
        # make the hue get its maximum dynamic saturation, up till maximum green, then linearly decreasing
        e = max(r, g, b)
        p = min(1.0, (1.0 - ll / e) / (1.0 - br), (1.0 - ll * led_balance[1]) / (1.0 - led_brightness[1]))
        t1 = ll * p / ((br - e) * p + e)
        t2 = max(0.0, ll - t1 * br)
    t1 = s * t1
    t2 = s * t2 + ll * (1.0 - s)
    return rgb_color(r * t1 + t2, g * t1 + t2, b * t1 + t2)
