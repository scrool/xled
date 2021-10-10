from xled.control import HighControlInterface
from xled.discover import discover
import time

dev = discover()

# Start of test sequence

ctr = HighControlInterface(dev.ip_address)

ctr.get_formatted_timer()

ctr.set_formatted_timer("18:59:00", "19:00:00")

ctr.get_formatted_timer()

ctr.disable_timer()

ctr.get_formatted_timer()

ctr.turn_on()

ctr.is_on()

ctr.turn_off()

ctr.show_demo(3)

ctr.show_effect(2)

def blendcolors(rgb1, rgb2, prop):
    return tuple(map(lambda c1, c2: int(round(c1 + (c2 - c1) * prop)), rgb1, rgb2))

m1 = ctr.make_empty_movie()

for i in range(0, 21):
    ctr.add_to_movie(m1, ctr.make_solid_pattern(blendcolors((230, 0, 0), (0, 255, 0), i/20.0)))

m2 = ctr.make_func_movie(21, lambda i: ctr.make_solid_pattern(blendcolors((0, 255, 0), (0, 0, 163), i/20.0)))

lst = [ctr.make_solid_pattern(blendcolors((0, 0, 163), (230, 0, 0), i/20.0)) for i in range(0, 21)]

m3 = ctr.to_movie(lst)

ctr.is_pattern(lst[0])

ctr.is_movie(m3)

ctr.show_movie(m1, 5)

ctr.show_movie(m2, 5)

ctr.upload_movie(m3, 5)

ctr.show_playlist([0, 1, 2], 10)

ctr.clear_movies()

numleds = ctr.get_device_info()['number_of_led']

pat = ctr.make_solid_pattern((0, 0, 0))

for i in range(0, 10):
    pat = ctr.modify_pattern(pat, i*7, (230, 255, 163))

perm = list(reversed(range(0, numleds)))

ctr.show_pattern(pat)

pat = ctr.permute_pattern(pat, perm, circular=True)

ctr.show_pattern(pat)

pat = ctr.make_func_pattern(lambda i: blendcolors((230, 0, 82), (0, 255, 82), abs(i-numleds//2)*2.0/numleds), circular=True)

for i in range(0, 3*numleds):
    ctr.show_rt_frame(pat)
    time.sleep(0.02)
    pat = ctr.rotate_pattern(pat, 1, circular=True)

for i in range(0, 3*numleds):
    pat = ctr.make_layout_pattern(lambda pos: blendcolors((230, 0, 82), (0, 255, 82), abs(((pos[0] + pos[1] + float(i)/numleds) % 2.0) - 1.0)), style='square')
    ctr.show_rt_frame(pat)
    time.sleep(0.02)

ctr.save_movie("testmovie.txt", m1, 8)

(m4, fps) = ctr.load_movie("testmovie.txt")

ctr.show_movie(m4, fps)

ctr.turn_off()

# End of test sequence
