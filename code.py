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
import asyncio
import board
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


## --------------- Async Tasks -------------------

async def scroll_task():
    while True:
        await gfx.scroll_next_label_async()
        await asyncio.sleep(SCROLL_HOLD_TIME)


async def network_task():
    global localtime_refresh, weather_refresh, power_refresh, bottom_refresh, bottom_mode

    while True:
        try:
            if not network.is_connected:
                print("Not connected, rebooting...")
                microcontroller.reset()

            if (time.localtime()[3] > 5) and (time.localtime()[3] < 22):
                matrix.display.brightness = 0.1

                # Reset local time timer once per hour (NTP call disabled)
                if (not localtime_refresh) or (time.monotonic() - localtime_refresh) > 3600:
                    print("***** Executing Time")
                    localtime_refresh = time.monotonic()

                # Weather every 10 minutes (only if time was not just refreshed)
                elif (not weather_refresh) or (time.monotonic() - weather_refresh) > 600:
                    print("***** Executing Weather")
                    try:
                        value = network.fetch_data(DATA_SOURCE, json_path=(DATA_LOCATION,))
                        gfx.display_weather(value)
                    except Exception as e:
                        print("Weather error, retrying! -", e)
                        microcontroller.reset()
                    weather_refresh = time.monotonic()

                # Power load + battery every 10 seconds
                elif (not power_refresh) or (time.monotonic() - power_refresh) > 10:
                    print("***** Executing Power")
                    headers = {
                        "Authorization": f"Bearer {BEARER_TOKEN}",
                        "Content-Type": "application/json",
                    }
                    try:
                        value_load = network.fetch_data(DATA_SOURCE_POWER_LOAD, headers=headers, json_path=(DATA_LOCATION,))
                    except Exception as e:
                        print("Power error, retrying! -", e)
                        microcontroller.reset()
                        await asyncio.sleep(0)
                        continue

                    # Battery is best-effort: a bad entity ID must not reboot
                    value_battery = None
                    try:
                        value_battery = network.fetch_data(DATA_SOURCE_POWER_BATTERY, headers=headers, json_path=(DATA_LOCATION,))
                    except Exception as e:
                        print("Battery fetch skipped: ", e)

                    gfx.store_data(value_load, value_battery)
                    power_refresh = time.monotonic()

                # Alternate bottom panel every 5 seconds (independent of fetches)
                if (not bottom_refresh) or (time.monotonic() - bottom_refresh) > 5:
                    bottom_mode = not bottom_mode
                    gfx.show_bottom(bottom_mode)
                    bottom_refresh = time.monotonic()

            else:
                print("Hour: " + str(time.localtime()[3]) + " - they are all sleeping :-)")
                matrix.display.brightness = 0
                await asyncio.sleep(60)
                continue

        except Exception as e:
            print("Generic error, retrying! -", e)
            await asyncio.sleep(5)
            continue

        await asyncio.sleep(0)


async def main():
    asyncio.create_task(network_task())
    await scroll_task()


gc.collect()
asyncio.run(main())
