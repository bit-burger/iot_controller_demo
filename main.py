import network
from machine import Pin
from neopixel import NeoPixel

import gc
import uasyncio as asyncio
import ujson
import ure as re
from server.web import WebApp, jsonify

np = NeoPixel(Pin(4), 12)   # create NeoPixel driver on GPIO4 for 12 pixels

def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('_homezone_', '')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())


print("init")
do_connect()
print("connected")
webapp = WebApp()

async def flushLEDs():
  np.write()
  gc.collect()

@webapp.route('/led', method='GET')
def get_led(request, response):
    yield from jsonify(response, {np[0]})

@webapp.route((re.compile('^/led/(.+)')), method='PUT')
def set_led(request, response):
    yield from request.parse_json_data()
    led = int(request.url_match.group(1))    
    np[led] = (request.jsondata['r'], request.jsondata['g'], request.jsondata['b'])
    asyncio.create_task(flushLEDs())
    yield from jsonify(response, np[led])


def main():
    """
    Set up the tasks and start the event loop
    """    
    loop = asyncio.get_event_loop()
    loop.create_task(asyncio.start_server(webapp.handle, '0.0.0.0', 80))
    gc.collect()
    loop.run_forever()


np[0] = (255, 255, 255) # set the first pixel to white
np.write()              # write data to all pixels
#r, g, b = np[0]         # get first pixel colour

main()