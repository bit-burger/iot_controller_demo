import network
from machine import Pin
from neopixel import NeoPixel

import gc
import uasyncio as asyncio
import ujson
import ure as re
from server.web import WebApp, jsonify

np = NeoPixel(Pin(4), 12)   # create NeoPixel driver on GPIO4 for 12 pixels
webapp = WebApp()

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

#flush the gpio and gc collect, call async via asyncio.create_task(flushLEDs())
async def flushLEDs():
  np.write()
  gc.collect()

#sets all LEDS at once, returns status of all leds
@webapp.route('/leds', method='PUT')
def set_leds(request, response):
    yield from request.parse_json_data()
    led_data = request.jsondata
    if len(led_data) == 12:
        for i in range(len(led_data)):
            np[i] = (led_data[i][0], led_data[i][1], led_data[i][2])
        asyncio.create_task(flushLEDs())
    yield from jsonify(response, list(np))


#switch all leds off, returns status of all leds
@webapp.route('/leds/off', method='GET')
def set_leds_off(request, response):
    for j in range(np.n):
         np[j] = (0, 0, 0)
    np.write()
    yield from jsonify(response, list(np))

#get status of all leds
@webapp.route('/leds', method='GET')
def get_led(request, response):
    yield from jsonify(response, {np})

#control one led
@webapp.route((re.compile('^/led/(.+)')), method='PUT')
def set_led(request, response):
    yield from request.parse_json_data()
    led = int(request.url_match.group(1))    
    np[led] = (request.jsondata['r'], request.jsondata['g'], request.jsondata['b'])
    asyncio.create_task(flushLEDs())
    yield from jsonify(response, np[led])

def setup():
    print("init")
    do_connect()
    print("connected")
    
def main():
    """
    Set up the tasks and start the event loop
    """        
    loop = asyncio.get_event_loop()
    loop.create_task(asyncio.start_server(webapp.handle, '0.0.0.0', 80))
    gc.collect()
    loop.run_forever()

setup()
main()