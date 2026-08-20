# SPDX-FileCopyrightText: 2020 John Park for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# Matrix Weather display
# For Metro M4 Airlift with RGB Matrix shield, 64 x 32 RGB LED Matrix display

"""
This example queries the Open Weather Maps site API to find out the current
weather for your location... and display it on a screen!
if you can find something that spits out JSON data, we can display it
"""
import os
import gc
import time
import board
import displayio
import microcontroller

from digitalio import DigitalInOut, Direction, Pull
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix

import openweather_graphics  # pylint: disable=wrong-import-position


### ------------- Portal Matrix origingal Setup ----------------

if hasattr(board, "D12"):
    jumper = DigitalInOut(board.D12)
    jumper.direction = Direction.INPUT
    jumper.pull = Pull.UP
    is_metric = jumper.value
elif hasattr(board, "BUTTON_DOWN") and hasattr(board, "BUTTON_UP"):
    button_down = DigitalInOut(board.BUTTON_DOWN)
    button_down.switch_to_input(pull=Pull.UP)

    button_up = DigitalInOut(board.BUTTON_UP)
    button_up.switch_to_input(pull=Pull.UP)
    if not button_down.value:
        print("Down Button Pressed")
        microcontroller.nvm[0] = 1
    elif not button_up.value:
        print("Up Button Pressed")
        microcontroller.nvm[0] = 0
    print(microcontroller.nvm[0])
    is_metric = microcontroller.nvm[0]
else:
    is_metric = False

if is_metric:
    UNITS = "metric"  # can pick 'imperial' or 'metric' as part of URL query
    print("Jumper set to metric")
else: 
    UNITS = "imperial"
    print("Jumper set to imperial")

# Use cityname, country code where countrycode is ISO3166 format.
# E.g. "New York, US" or "London, GB"
LOCATION = "Inzago, IT"
print("Getting weather for {}".format(LOCATION))
# Set up from where we'll be fetching data
DATA_SOURCE = (
    "http://api.openweathermap.org/data/2.5/weather?q=" + LOCATION + "&units=" + UNITS
)
DATA_SOURCE += "&appid=" + os.getenv("OPENWEATHER_TOKEN")
# You'll need to get a token from openweather.org, looks like 'b6907d289e10d714a6e88b30761fae22'
# it goes in your secrets.py file on a line such as:
# 'openweather_token' : 'your_big_humongous_gigantor_token',
DATA_LOCATION = []
SCROLL_HOLD_TIME = 0  # set this to hold each line before finishing scroll
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
 
# --- Power setup ---
DATA_SOURCE_POWER_LOAD    = "http://192.168.1.15:8123/api/states/sensor.tesla_power_wall_load_power"
DATA_SOURCE_POWER_SITE    = "http://192.168.1.15:8123/api/states/sensor.tesla_power_wall_grid_power"
DATA_SOURCE_POWER_BATTERY = "http://192.168.1.15:8123/api/states/sensor.croods_home_charge"



# --- Display setup ---
matrix = Matrix(width=64, height=64)
matrix.display.root_group = displayio.Group()  # blank screen — hides CircuitPython boot logo
network = Network(status_neopixel=board.NEOPIXEL)#, debug=True)

if UNITS in ("imperial", "metric"):
    gfx = openweather_graphics.OpenWeather_Graphics(
        matrix.display, am_pm=True, units=UNITS
    )
print("gfx loaded")


# Variables to manage refresh
localtime_refresh = None
weather_refresh = None
power_refresh = None
battery_refresh = None
bottom_refresh = None
bottom_mode = True  # True = show power load, False = show battery %


# ------------- Wifi  Setup ------------- #
MAX_RETRIES = 5
retry_count = 0
while retry_count < MAX_RETRIES:
    try:
        network.connect() 
        network.get_local_time()
        break
    except Exception as e:
        print(f"Error: {e}")
        retry_count += 1
        #matrix.set_text(f"Retrying... {retry_count}/{MAX_RETRIES}")
        time.sleep(5)  # Wait before retrying

if retry_count == MAX_RETRIES:
    print("Failed to connect after retries.")
    #matrix.set_text("No Connection")
    microcontroller.reset()


## --------------- Loop Start -------------------
while True:
    #We need to execute only one request per loop
    RequestExecuted = False

    try:
        
        if network.is_connected == False:
            print("*************************************")
            print("We are not connected, rebooting...")
            microcontroller.reset()
                
            
        # Execute only if we are in the correct timeframe
        # print("Local Time: ", time.localtime()[3])
        if ((time.localtime()[3] > 5) & (time.localtime()[3] < 22 )):

            matrix.display.brightness = 0.1

            # only query the online time once per hour (and on first run)
            if (not localtime_refresh) or (time.monotonic() - localtime_refresh) > 3600:
                print("***** Executing Time")
                try:
                    RequestExecuted = True
                    #print("Getting time from internet!")
                    #network.get_local_time()
                    localtime_refresh = time.monotonic()

                except Exception as e:
                    print("Some error getting Time occured, retrying! -", e) 
                    microcontroller.reset()
                    continue

            # only query the weather every 10 minutes (and on first run)
            if (not RequestExecuted) and ((not weather_refresh) or (time.monotonic() - weather_refresh) > 600):
                print("***** Executing Weather - ", end="")
                try:
                    RequestExecuted = True
                    value = network.fetch_data(DATA_SOURCE, json_path=(DATA_LOCATION,))
                    #print("Response is", value)
                    gfx.display_weather(value)
                    
                except Exception as e:
                    print("Some error on Weather occured, retrying! -", e)
                    microcontroller.reset()
                    continue

                weather_refresh = time.monotonic()

            # query power load every 10 seconds — one request, fast
            if (not RequestExecuted) and ((not power_refresh) or (time.monotonic() - power_refresh) > 10):
                print("***** Executing Power - ", end="")
                headers = {
                    "Authorization": f"Bearer {BEARER_TOKEN}",
                    "Content-Type": "application/json",
                }
                try:
                    value_load = network.fetch_data(DATA_SOURCE_POWER_LOAD, headers=headers, json_path=(DATA_LOCATION,))
                except Exception as e:
                    print("Some error on Power occured, retrying! -", e)
                    microcontroller.reset()
                    continue
                gfx.store_data(value_load, None)
                power_refresh = time.monotonic()
                RequestExecuted = True

            # query battery separately every 60 seconds — changes slowly, no need for same cadence
            elif (not RequestExecuted) and ((not battery_refresh) or (time.monotonic() - battery_refresh) > 60):
                print("***** Executing Battery - ", end="")
                headers = {
                    "Authorization": f"Bearer {BEARER_TOKEN}",
                    "Content-Type": "application/json",
                }
                try:
                    value_battery = network.fetch_data(DATA_SOURCE_POWER_BATTERY, headers=headers, json_path=(DATA_LOCATION,))
                    gfx.store_data(None, value_battery)
                except Exception as e:
                    print("Battery fetch skipped: ", e)
                battery_refresh = time.monotonic()
                RequestExecuted = True

            # Scroll first so the animation is never interrupted mid-label.
            # Any fetch pause falls at the natural transition between labels.
            gfx.scroll_next_label()

            # Alternate bottom panel between power load and battery every 5 seconds
            if (not bottom_refresh) or (time.monotonic() - bottom_refresh) > 5:
                bottom_mode = not bottom_mode
                gfx.show_bottom(bottom_mode)
                bottom_refresh = time.monotonic()
                
        else:
            print("Current hour: " + str(time.localtime()[3]) + " they are all sleeping :-)")
            #value = network.fetch_data(DATA_SOURCE_POWER, json_path=(DATA_LOCATION,))
            #gfx.display_empty()
            matrix.display.brightness = 0
            time.sleep(60)
            continue



    except Exception as e:
        print("Some error generic occured, retrying! -", e)
        time.sleep(5)
        continue

    # Pause between labels
    time.sleep(SCROLL_HOLD_TIME)
