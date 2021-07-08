import machine
import time
from neopixel import NeoPixel

import gc
import uasyncio as asyncio
import ujson
import ure as re
from server.web import WebApp, jsonify, plain_text_start_response, start_response
from wifi import *
from HTU21D import *

np = NeoPixel(Pin(4), 12)   # create NeoPixel driver on GPIO4 for 12 pixels
webapp = WebApp()
htu21d = HTU21D(22, 21)
animation = None

# flush the gpio and gc collect, call async via asyncio.create_task(flushLEDs())


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


# sets all LEDS at once, returns status of all leds
@webapp.route('/leds', method='PUT')
def set_leds(request, response):
    if animation != None:
        yield from start_response(response, status='409')
        return
    yield from request.parse_json_data()
    led_data = request.jsondata
    if len(led_data) == 12:
        for i in range(len(led_data)):
            np[i] = (led_data[i][0], led_data[i][1], led_data[i][2])
        asyncio.create_task(flushLEDs())
    yield from jsonify(response, list(np))

# return current sensor data


@webapp.route('/sensors', method='GET')
def get_sensor_data(request, response):
    yield from jsonify(response, {'temperature': htu21d.temperature, 'humidity': htu21d.humidity})
# [
# {"frame": [[12,12,12],[12,12,12],[12,12,12]], "time": 23.0}
# {"frame": [[234,234,234],[234,234,234],[134,46,152]], "time": 3.0}
# ]


def vVal(val):
    return val >= 0 and val <= 255

def check_for_animation(response):
    yield from plain_text_start_response(response, 'A animation is running, cancel it to use the leds', status='409')

class Animation:
    def __init__(self, task, end_frame):
        self.task = task
        self.end_frame = end_frame

def asignNp(npList):
    global np
    for i in range(np.n):
        np[i] = npList[i]
    asyncio.create_task(flushLEDs())

@webapp.route('/cancel-animation', method='DELETE')
def cancel_animation(request, response):
    global animation
    if animation != None:
        animation.task.cancel()
        asignNp(animation.end_frame)
        animation = None
        yield from start_response(response)
    else:
        yield from start_response(response, status='409')
        print('Error in canceling')


@webapp.route('/animation', method='POST')
def animate_leds(request, response):
    if animation != None:
        yield from start_response(response, status='409')
        return
    yield from request.parse_json_data()
    animation_frames = request.jsondata['frames']
    try:
        repeat = request.jsondata['repeat']
        if(repeat < 1):
            raise Exception('Repeat has to be at least one')
        if(len(animation_frames) < 1):
            raise Exception('There has to be at least one animation_frame')
        for frame in animation_frames:
            if(frame['time'] <= 0):
                raise Exception(
                    'The time between each frame has to be greater than 0 seconds')
            if(frame['time'] > 60):
                raise Exception(
                    'The time between each frame is not allowed to be bigger than 60 seconds')
            if(len(frame['frame']) != 12):
                raise Exception('Each frame should contain 12 rgb values')
            for val in frame['frame']:
                if(not (vVal(val[0]) and vVal(val[0]) and vVal(val[0]))):
                    raise Exception(
                        'Each of the red green and blue values should be between 0 and 255')
        asyncio.create_task(animating_procedre(animation_frames, repeat))
        yield from start_response(response)
    except (Exception, KeyError) as e:
        print('Error')
        print(animation_frames)
        print(e.__class__)
        if(e is Exception):
            print(e.args)
        else:
            print(e.args)
        response.write()
        yield from start_response(response, status='401')



async def animating_procedre(animation_frames, repeat):
    end_frame = []
    for i in range(np.n):
        end_frame.append(np[i])
    task = asyncio.create_task(animate(animation_frames, repeat, end_frame))
    global animation
    animation = Animation(task, end_frame)


async def animate(animation_frames, repeat, end_frame):
    while repeat > 0:
        for frame in animation_frames:
            led_data = frame["frame"]
            led_time = frame["time"]
            print(led_data)
            print(led_time)
            for i in range(len(led_data)):
                np[i] = (led_data[i][0], led_data[i][1], led_data[i][2])
            asyncio.create_task(flushLEDs())
            await asyncio.sleep(led_time)
        repeat -= 1
    global animation
    animation = None
    asignNp(end_frame)


# switch all leds off, returns status of all leds
@webapp.route('/leds/off', method='GET')
def set_leds_off(request, response):
    if animation != None:
        yield from start_response(response, status='409')
        return
    for j in range(np.n):
        np[j] = (0, 0, 0)
    np.write()
    yield from jsonify(response, list(np))

# get status of all leds


@webapp.route('/leds', method='GET')
def get_led(request, response):
    if animation != None:
        yield from start_response(response, status='409')
        return
    yield from jsonify(response, list(np))

# control one led


@webapp.route((re.compile('^/led/(.+)')), method='PUT')
def set_led(request, response):
    if animation != None:
        yield from start_response(response, status='409')
        return
    yield from request.parse_json_data()
    led = int(request.url_match.group(1))
    np[led] = (request.jsondata['r'],
               request.jsondata['g'], request.jsondata['b'])
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
        request.form['ssid']: request.form['password']
    }
    write_profiles(wifi_data)
    asyncio.create_task(reset())
    yield from jsonify(response, request.form)


def leds_init():
    for j in range(np.n):
        np[j] = (255, 255, 255)
    np.write()
    time.sleep(1)
    for j in range(np.n):
        np[j] = (0, 0, 0)
    np.write()


async def reset():
    print("reset")
    await asyncio.sleep(2)
    print("now")
    machine.reset()


def setup():
    print("init")
    leds_init()
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
