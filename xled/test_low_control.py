from xled.control import ControlInterface
from xled.discover import discover

import io
import struct
import time

def make_solid_movie(ctr, r, g, b):
    num_leds = ctr.get_device_info()['number_of_led']
    pat = [struct.pack(">BBB", r, g, b)] * num_leds
    movie = io.BytesIO()
    movie.write(b''.join(pat))
    movie.seek(0)
    return movie

def rotate90(coords):
    return [{'x': 1.0-2*ele['y'], 'y': (ele['x']+1.0)/2, 'z': ele['z']}
            for ele in coords]

dev = discover()

# Start of test sequence

ctr = ControlInterface(dev.ip_address, dev.hw_address)

ctr.check_status()._data

ctr.firmware_version()._data

vers = tuple(map(int, ctr.firmware_version()['version'].split('.')))

ctr.get_device_info()._data

numleds = ctr.get_device_info()['number_of_led']

name = ctr.get_device_name()['name']

ctr.set_device_name("Dummyname")._data

ctr.get_device_name()._data

ctr.set_device_name(name)._data

ctr.get_led_config()._data

ctr.get_network_status()._data

ctr.network_scan()._data

time.sleep(1)
ctr.network_scan_results()._data

ctr.set_timer(3600, 7200)._data

ctr.get_timer()._data

ctr.set_timer(-1, -1)._data

ctr.get_mode()._data

ctr.set_mode('effect')

ctr.get_mode()._data

ctr.get_led_effects()._data

ctr.get_led_effects_current()._data

ctr.set_led_effects_current(2)._data

ctr.led_reset()._data

if vers > (2, 4, 2):

    res = ctr.get_mqtt_config()._data

    ctr.set_mqtt_config("127.0.0.1", None, res['client_id'], 'Pizza', 3600)._data

    ctr.get_mqtt_config()._data

    ctr.set_mqtt_config(res['broker_host'], res['broker_port'], res['client_id'], res['user'], res['keep_alive_interval'])._data

    ctr.get_brightness()._data

    ctr.set_brightness(50)._data

    ctr.get_brightness()._data

    ctr.set_brightness(-20, relative=True)._data

    ctr.get_brightness()._data

    ctr.set_brightness(100, enabled=False)._data

    ctr.get_saturation()._data

    ctr.set_saturation(90)._data

    ctr.get_saturation()._data

    ctr.set_saturation(-30, relative=True)._data

    ctr.get_saturation()._data

    ctr.set_saturation(+80, enabled=False, relative=True)._data

    ctr.get_saturation()._data

m_white = make_solid_movie(ctr, 230, 255, 160)
m_green = make_solid_movie(ctr, 0, 255, 0)
m_yellow = make_solid_movie(ctr, 230, 170, 0)
m_lime = make_solid_movie(ctr, 100, 255, 0)
m_orange = make_solid_movie(ctr, 230, 85, 0)

ctr.get_led_movie_config()._data

ctr.set_led_movie_full(m_white)

ctr.set_led_movie_config(1000, 1, numleds)

ctr.set_mode('movie')

if vers > (2, 5, 6):

    ctr.get_movies()._data

    ctr.get_movies_current()._data

    ctr.set_movies_new("green", "00000000-0000-0000-000A-000000000001", "rgb_raw", numleds, 1, 1)._data

    ctr.set_movies_full(m_green)._data

    ctr.set_movies_new("lime", "00000000-0000-0000-000A-000000000002", "rgb_raw", numleds, 1, 1)

    ctr.set_movies_full(m_lime)._data

    ctr.get_movies_current()._data

    ctr.set_movies_current(1)._data

    lst = ctr.get_movies()['movies']

    pl = [{'unique_id': ele['unique_id'], 'duration': 5} for ele in lst]

    ctr.get_playlist()._data

    ctr.set_playlist(pl)._data

    ctr.get_playlist()._data

    ctr.set_mode('playlist')

    ctr.get_playlist_current()._data

    ctr.set_playlist_current(2)._data

    ctr.delete_playlist()._data

    ctr.get_mode()._data

    ctr.set_mode('effect')

    ctr.delete_movies()._data

    ctr.get_movies()._data

m_yellow.seek(0)
m_orange.seek(0)
m_lime.seek(0)
m_green.seek(0)

ctr.set_mode('rt')

ctr.set_rt_frame_rest(m_orange)

ctr.set_rt_frame_socket(m_yellow, 1, min(255, numleds))

ctr.set_rt_frame_socket(m_lime, 2)

ctr.set_rt_frame_socket(m_green, 3)

if vers > (2, 4, 2):  # Uncertain about first version with layout

    ctr.set_mode('effect')

    layout = ctr.get_led_layout()._data

    ctr.set_led_layout(layout['source'], rotate90(layout['coordinates']), layout['synthesized'])

ctr.set_mode('off')

# End of test sequence
