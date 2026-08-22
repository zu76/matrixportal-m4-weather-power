# SPDX-FileCopyrightText: 2020 John Park for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import time
import displayio
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font

from adafruit_progressbar.horizontalprogressbar import (
    HorizontalProgressBar,
    HorizontalFillDirection,
    )

TEMP_COLOR = 0xFFA800
GREEN_COLOR = 0x33FF33
YELLOW_COLOR = 0xFFFF00
RED_COLOR = 0xE60000
BATTERY_COLOR = 0x00AAFF  # blue for battery label prefix

MAIN_COLOR = 0x9000FF  # weather condition
DESCRIPTION_COLOR = 0x00D3FF
CITY_COLOR = 0x9000FF
HUMIDITY_COLOR = 0x0000AA
WIND_COLOR = 0xCCCCCC
TIME_COLOR = 0xFFFFFF

cwd = ("/" + __file__).rsplit("/", 1)[
    0
]  # the current working directory (where this file is)

small_font = cwd + "/fonts/Arial-12.bdf"
medium_font = cwd + "/fonts/Arial-14.bdf"

icon_spritesheet = cwd + "/weather-icons.bmp"
icon_width = 16
icon_height = 16
scrolling_text_height = 24
scroll_delay = 0.03


class OpenWeather_Graphics(displayio.Group):
    def __init__(
            self,
            display,
            *,
            am_pm=True,
            units="imperial"
    ):
        super().__init__()
        self.am_pm = am_pm
        if units == "metric":
            self.celsius = True
            self.meters_speed = True
        else:
            self.celsius = False
            self.meters_speed = False
        self.display = display

        splash = displayio.Group()
        # CircuitPython 6 & 7 compatible
        background = displayio.OnDiskBitmap(open("loading.bmp", "rb"))
        bg_sprite = displayio.TileGrid(
            background,
            pixel_shader=getattr(background, 'pixel_shader', displayio.ColorConverter()),
        )
        # # CircuitPython 7+ compatible
        # background = displayio.OnDiskBitmap("loading.bmp")
        # bg_sprite = displayio.TileGrid(background, pixel_shader=background.pixel_shader)

        splash.append(bg_sprite)
        #display.show(splash)
        display.root_group = splash

        self.root_group = displayio.Group()
        self.root_group.append(self)
        self._icon_group = displayio.Group()
        self.append(self._icon_group)
        self._text_group = displayio.Group()
        self.append(self._text_group)
        self._scrolling_group = displayio.Group()
        self.append(self._scrolling_group)

        # ALB
        self._power_group = displayio.Group()
        self.append(self._power_group)

        self._power_bar = HorizontalProgressBar(
            (2, 58), (60, 3),
            0,
            6500,
            value=5,
            bar_color=0x11FF11,
            fill_color=0x333333,
            border_thickness=0,
            margin_size=0,
            )
        self.append(self._power_bar)

        # The label index we're currently scrolling
        self._current_label = None

        # Load the icon sprite sheet
        # CircuitPython 6 & 7 compatible
        icons = displayio.OnDiskBitmap(open(icon_spritesheet, "rb"))
        self._icon_sprite = displayio.TileGrid(
            icons,
            pixel_shader=getattr(icons, 'pixel_shader', displayio.ColorConverter()),
            tile_width=icon_width,
            tile_height=icon_height
        )
        # # CircuitPython 7+ compatible
        # icons = displayio.OnDiskBitmap(icon_spritesheet)
        # self._icon_sprite = displayio.TileGrid(
        #     icons,
        #     pixel_shader=icons.pixel_shader,
        #     tile_width=icon_width,
        #     tile_height=icon_height
        # )

        self.set_icon(None)
        self._scrolling_texts = []

        self.small_font = bitmap_font.load_font(small_font)
        self.medium_font = bitmap_font.load_font(medium_font)
        glyphs = b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-,.: "
        self.small_font.load_glyphs(glyphs)
        self.medium_font.load_glyphs(glyphs)
        self.medium_font.load_glyphs(("°",))  # a non-ascii character we need for sure

        self.city_text = None

        self.temp_text = Label(self.medium_font)
        self.temp_text.x = 20
        self.temp_text.y = 7
        self.temp_text.color = TEMP_COLOR
        self._text_group.append(self.temp_text)

        self.power_text = Label(self.medium_font)
        self.power_text.x = 1
        self.power_text.y = 45
        self.power_text.color = GREEN_COLOR
        self._power_group.append(self.power_text)

        self.description_text = Label(self.small_font)
        self.description_text.color = DESCRIPTION_COLOR
        self._scrolling_texts.append(self.description_text)

        self.humidity_text = Label(self.small_font)
        self.humidity_text.color = HUMIDITY_COLOR  #
        self._scrolling_texts.append(self.humidity_text)

        self.wind_text = Label(self.small_font)
        self.wind_text.color = WIND_COLOR
        self._scrolling_texts.append(self.wind_text)

        self.time_text = Label(self.small_font, text="--:--")
        self.time_text.color = TIME_COLOR
        self._scrolling_texts.append(self.time_text)

    def display_empty(self):
        #power0 = power["emeters"][0]["power"]
        print (self)
        self.display.root_group() #.show()
        matrixportal.set_text(".", 4)


    def display_power(self, power, power1=None):
        """
        power0 = power["emeters"][0]["power"]
        power1 = power["emeters"][1]["power"]
        powerTotal = int(power0 + power1)
        print("Power 0: " + str(power0))
        print("Power 1: " + str(power1))
        
        """
        #print("Debug " + power["state"])
        powerTotal = int(float(power["state"])) # in precedenza era in migliaia, ora rimosso il *1000
        #print("Total Power: " + str(powerTotal))

        powerText = str(powerTotal)

        if len(powerText) == 3 :
            powerText = " " + powerText
        self.power_text.text = powerText + "W"

        # 5
        if powerTotal > 6000:
            bar_color_to_set = RED_COLOR # red
            self.power_text.color = RED_COLOR
        elif powerTotal >5000:
            bar_color_to_set = YELLOW_COLOR # yellow
            self.power_text.color = YELLOW_COLOR
        else:
            bar_color_to_set = GREEN_COLOR # green
            self.power_text.color = GREEN_COLOR


        #bar_color_to_set = (0x20 * 2 + 20, (0x20 * (2 - 1)) + 20, 0x10)
        #print ("Bar BG Color " + str(bar_color_to_set))
        self._power_bar.bar_color = bar_color_to_set

        if powerTotal > 6500:
            self._power_bar.value = 6500
        else:
            self._power_bar.value = powerTotal

    def store_data(self, power, battery):
        if power is not None:
            self._last_power = power
        if battery is not None:
            self._last_battery = battery

    def display_battery(self, battery):
        pct = int(float(battery["state"]))

        text = str(pct) + "%"
        if len(text) < 4:
            text = " " + text
        self.power_text.text = text

        if pct <= 10:
            color = RED_COLOR
        elif pct <= 20:
            color = YELLOW_COLOR
        else:
            color = BATTERY_COLOR

        self.power_text.color = color
        self._power_bar.bar_color = color
        # Scale 0–100% into the bar's 0–6500 range
        self._power_bar.value = int(pct * 65)

    def display_time(self):
        t = time.localtime()
        self.time_text.text = "%02d:%02d" % (t[3], t[4])

    def show_bottom(self, is_power):
        if is_power:
            if hasattr(self, "_last_power") and self._last_power is not None:
                self.display_power(self._last_power)
        else:
            if hasattr(self, "_last_battery") and self._last_battery is not None:
                self.display_battery(self._last_battery)



    def display_weather(self, weather):
        # set the icon
        self.set_icon(weather["weather"][0]["icon"])

        temperature = weather["main"]["temp"]
        print(temperature)
        if self.celsius:
            self.temp_text.text = "%d°C" % temperature
        else:
            self.temp_text.text = "%d°F" % temperature

        description = weather["weather"][0]["description"]
        description = description[0].upper() + description[1:]
        print(description)
        self.description_text.text = description
        # "thunderstorm with heavy drizzle"

        humidity = weather["main"]["humidity"]
        print(humidity)
        self.humidity_text.text = "%d%% RH" % humidity

        wind = weather["wind"]["speed"]
        print(wind)
        if self.meters_speed:
            self.wind_text.text = "%d m/s" % wind
        else:
            self.wind_text.text = "%d mph" % wind
        
        self.display.root_group = self.root_group
        

    def set_icon(self, icon_name):
        """Use icon_name to get the position of the sprite and update
        the current icon.

        :param icon_name: The icon name returned by openweathermap

        Format is always 2 numbers followed by 'd' or 'n' as the 3rd character
        """

        icon_map = ("01", "02", "03", "04", "09", "10", "11", "13", "50")

        print("Set icon to", icon_name)
        if self._icon_group:
            self._icon_group.pop()
        if icon_name is not None:
            row = None
            for index, icon in enumerate(icon_map):
                if icon == icon_name[0:2]:
                    row = index
                    break
            column = 0
            if icon_name[2] == "n":
                column = 1
            if row is not None:
                self._icon_sprite[0] = (row * 2) + column
                self._icon_group.append(self._icon_sprite)

    def scroll_next_label(self):
        # Start by scrolling current label off if not set to None
        if self._current_label is not None and self._scrolling_group:
            current_text = self._scrolling_texts[self._current_label]
            text_width = current_text.bounding_box[2]
            for _ in range(text_width + 1):
                self._scrolling_group.x = self._scrolling_group.x - 1
                time.sleep(scroll_delay)

        if self._current_label is not None:
            self._current_label += 1
        if self._current_label is None or self._current_label >= len(
                self._scrolling_texts
        ):
            self._current_label = 0

        # Setup the scrolling group by removing any existing
        if self._scrolling_group:
            self._scrolling_group.pop()
        # Then add the current label
        current_text = self._scrolling_texts[self._current_label]
        self._scrolling_group.append(current_text)

        # Set the position of the group to just off screen and centered vertically for lower half
        self._scrolling_group.x = self.display.width
        self._scrolling_group.y = 23

        # Run a loop until the label is offscreen again and leave function
        for _ in range(self.display.width):
            self._scrolling_group.x = self._scrolling_group.x - 1
            time.sleep(scroll_delay)
        # By blocking other code we will never leave the label half way scrolled
        #print("Scroll: " + str(self.display.width))
