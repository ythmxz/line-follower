#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import ColorSensor
from pybricks.parameters import (Port, Button)
from pybricks.tools import (DataLog, wait)

# Objects
ev3 = EV3Brick()
color_sensor = ColorSensor(Port.S1)
data = DataLog(
    "Branco",
    "Preto",
    name="logs/calibration/calibration",
    timestamp=False,
    extension="txt",
)

# Variables
sensor_value = 0  # Refletancia (%)


def wait_for_release():
    while Button.CENTER in ev3.buttons.pressed():
        wait(10)


def wait_for_press():
    while Button.CENTER not in ev3.buttons.pressed():
        wait(10)


def sample_until_press():
    values = []

    while Button.CENTER not in ev3.buttons.pressed():
        value = color_sensor.reflection()
        values.append(value)

        wait(10)

    return values


# Program
wait_for_release()
wait_for_press()
wait_for_release()
ev3.speaker.beep()

white_values = sample_until_press()
white_mean = sum(white_values) / len(white_values) if white_values else 0
ev3.speaker.beep()

wait_for_release()
wait_for_press()
wait_for_release()
ev3.speaker.beep()

black_values = sample_until_press()
black_mean = sum(black_values) / len(black_values) if black_values else 0
ev3.speaker.beep()

data.log(white_mean, black_mean)
