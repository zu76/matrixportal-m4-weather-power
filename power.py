# Controls
import displayio

from adafruit_progressbar.horizontalprogressbar import (
    HorizontalProgressBar,
    HorizontalFillDirection,
    )

class Power_Graphics(displayio.Group):
    def __init__(
            self,
            display,
            *
    ):
        super().__init__()
        self.display = display

        self.group = displayio.Group()
        """
        #PowerBar
        # Countdown to the start of the bars demo
        power_bar = HorizontalProgressBar(
            (2, 60),
            (20, 4),
            0,
            5,
            value=5,
            bar_color=0x11FF11,
            fill_color=0x333333,
            border_thickness=0,
            margin_size=0,
        )

        self.group.append(power_bar)
        self.display.show(self.group)
        """
    def getGroup():
        return self.group

    def display_power(self, power):
        a = 1
