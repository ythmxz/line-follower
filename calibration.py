#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import ColorSensor
from pybricks.parameters import (Port, Button)
from pybricks.tools import (DataLog, wait)

# Objects
ev3 = EV3Brick()
color_sensor = ColorSensor(Port.S1)
data = DataLog("sensor", name="calibration", timestamp=False, extension="txt")

# Variables
sensor_value = 0    # Refletância (%)

# Program
while Button.CENTER not in ev3.buttons.pressed():
    sensor_value = color_sensor.reflection()
    data.log(sensor_value)
    wait(10)
