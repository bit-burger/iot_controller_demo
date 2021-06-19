import machine
from neopixel import NeoPixel

import gc
import uasyncio as asyncio
import ujson
import ure as re
from server.web import WebApp, jsonify
from wifi import *
from HTU21D import *

np = NeoPixel(Pin(4), 12)   # create NeoPixel driver on GPIO4 for 12 pixels
webapp = WebApp()
htu21d = HTU21D(22,21)

#flush the gpio and gc collect, call async via asyncio.create_task(flushLEDs())
async def flushLEDs():
  np.write()
  gc.collect()

async def getSensorData():
    while True:
        t = htu21d.temperature
        h = htu21d.humidity
        fstr = 'Temp {:5.1f} Humidity {:5.1f}'
        print(fstr.format(t, h))
        await asyncio.sleep(5)


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

#return current sensor data
@webapp.route('/sensors', method='GET')
def get_sensor_data(request, response):
    yield from jsonify(response, {'temperature' : htu21d.temperature, 'humidity': htu21d.humidity})


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
    yield from jsonify(response, list(np))

#control one led
@webapp.route((re.compile('^/led/(.+)')), method='PUT')
def set_led(request, response):
    yield from request.parse_json_data()
    led = int(request.url_match.group(1))    
    np[led] = (request.jsondata['r'], request.jsondata['g'], request.jsondata['b'])
    asyncio.create_task(flushLEDs())
    yield from jsonify(response, np[led])

@webapp.route('/', method='GET')
def index(request, response):
    gc.collect()
    yield from webapp.sendfile(response, '/static/index.html')

@webapp.route('/configure_wifi', method='POST')
def wifi_config(request, response):
    gc.collect()
    yield from request.read_form_data()
    wifi_data = {
        request.form['ssid']:request.form['password']
    }
    write_profiles(wifi_data)
    asyncio.create_task(reset())
    yield from jsonify(response, request.form)

async def reset():
    print("reset")
    await asyncio.sleep(2)
    print("now")
    machine.reset()

def setup():
    print("init")
    setup_wifi()
    print("connected")    
    
def main():
    """
    Set up the tasks and start the event loop
    """        
    loop = asyncio.get_event_loop()
    loop.create_task(asyncio.start_server(webapp.handle, '0.0.0.0', 80))
    gc.collect()
    loop.create_task(getSensorData())
    loop.run_forever()

setup()
main()

