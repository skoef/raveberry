"""This module handles the led strip."""
from typing import Tuple


class Strip:
    """This class provides an interface to control the led strip."""

    def __init__(self) -> None:
        self.brightness = 1.0

        try:
            import Adafruit_PCA9685
        except ModuleNotFoundError:
            self.initialized = False
            return

        try:
            self.controller = Adafruit_PCA9685.PCA9685()
            self.initialized = True
        except (RuntimeError, OSError):
            # LED strip is not connected
            self.initialized = False

    def set_color(self, color: Tuple[float, float, float]) -> None:
        """Sets the color of the strip to the given rgb triple."""
        if not self.initialized:
            return

        for channel, val in enumerate(color):
            # map the value to the interval [0, 4095]
            dimmed_val = val * self.brightness
            scaled_val = round(dimmed_val * 4095)
            self.controller.set_pwm(channel, 0, scaled_val)

    def clear(self) -> None:
        """Turns off the strip by setting its color to black."""
        if not self.initialized:
            return

        for channel in range(3):
            self.controller.set_pwm(channel, 0, 0)
