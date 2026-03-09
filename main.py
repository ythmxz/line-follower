#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, ColorSensor)
from pybricks.parameters import Port, Button, Color
from pybricks.tools import wait

# Objects
ev3 = EV3Brick()
motor_left = Motor(Port.B)
motor_right = Motor(Port.C)
color_sensor = ColorSensor(Port.S1)

# Variables
speed = 200

# Program
while not Button.CENTER in ev3.buttons.pressed():
    if Button.UP in ev3.buttons.pressed():
        speed += 10

    elif Button.DOWN in ev3.buttons.pressed():
        speed -= 10

    if color_sensor.color() == Color.BLACK:
        motor_left.run(speed)
        motor_right.run(speed // 4)
        ev3.screen.print("RIGHT,", end=" ")

    else:
        motor_left.run(speed // 4)
        motor_right.run(speed)
        ev3.screen.print("LEFT,", end=" ")

    ev3.screen.print("(", motor_left.speed(), ", ", motor_right.speed(), ")")
    wait(10)
    ev3.screen.clear()

motor_left.stop()
motor_right.stop()
