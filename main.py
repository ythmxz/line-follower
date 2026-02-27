#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile


# This program requires LEGO EV3 MicroPython v2.0 or higher.
# Click "Open user guide" on the EV3 extension tab for more information.


# Create your objects here.
ev3 = EV3Brick()
motor_left = Motor(Port.B)
motor_right = Motor(Port.C)
color_sensor = ColorSensor(Port.S1)

SPEED: float = 200.0

# Write your program here.
while not ev3.buttons.pressed():
    if color_sensor.color() == Color.BLACK:
        motor_left.run(SPEED)
        motor_right.run(SPEED * 0.2)
    else:
        motor_left.run(SPEED * 0.2)
        motor_right.run(SPEED)

    wait(10)

motor_left.stop()
motor_right.stop()
