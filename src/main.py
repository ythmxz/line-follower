#!/usr/bin/env pybricks-micropython

from enum import Enum
from math import pi

from pybricks.ev3devices import ColorSensor, Motor
from pybricks.hubs import EV3Brick
from pybricks.parameters import Button, Port
from pybricks.tools import DataLog, StopWatch, wait


class ControllerType(Enum):
    NONE = "log"
    ON_OFF = "on_off"
    PROPORTIONAL = "proportional"
    PID = "pid"


controller_type = ControllerType.NONE


# Objects

ev3 = EV3Brick()
motor_left = Motor(Port.B)
motor_right = Motor(Port.C)
color_sensor = ColorSensor(Port.S1)

watch = StopWatch()
data = DataLog(
    # Environment
    "Tempo (s)",
    "Distância (m)",
    "Vel. Média (m/s)",
    # Sensor
    "Preto (%)",
    "Branco (%)",
    "Limite (%)",
    "Refletância (%)",
    "Erro (%)",
    # Control
    "Ganho Proporcional ((°/s)/%)",
    "Ganho Integral ((°/s)/%)",
    "Ganho Derivativo ((°/s)/%)",
    # Speed
    "Vel. Base (°/s)",
    "Correção (°/s)",
    "Vel. Angular Esq. (°/s)",
    "Vel. Angular Dir. (°/s)",
    # Curves
    "Suavidade Esq.(°/s)",
    "Suavidade Dir.(°/s)",
    "Oscilação",
    name=f"{controller_type.value}",
)

# Variables

# Timers
START_DELAY = 3_000
LOOP_DELAY = 10
MAX_TIME = 60_000

# Environment
time = 0
distance = 0
average_speed = 0

# Sensor
BLACK_DEFAULT = 8
WHITE_DEFAULT = 80

black = 0
white = 0

sensor_threshold = 0
sensor_value = 0
sensor_error = 0

# Control
proportional_gain = 2.0
integral_gain = 1.0
derivative_gain = 0.5

# Speed
base_speed = 100
correction = 50

left_speed = base_speed
previous_left_speed = left_speed

right_speed = base_speed
previous_right_speed = right_speed

# Curves
left_smoothness = 0
right_smoothness = 0

turns = 0
oscillation = 0
last_error_sign = 0

# Wheel
wheel_diameter = 56
wheel_circumference = pi * wheel_diameter

# Methods


# Environment
def calculate_distance(left_angle, right_angle, circumference):
    average_angle = (left_angle + right_angle) / 2

    return circumference * (average_angle / 360)


def calculate_average_speed(distance, elapsed_time):
    if elapsed_time > 0:
        return distance / elapsed_time

    return 0


# Control
def calculate_delta_time(current_time, previous_time):
    return (current_time - previous_time) / 1000


# Curves
def calculate_smoothness(current_speed, previous_speed):
    return abs(current_speed - previous_speed)


def calculate_oscillation(error, last_sign):
    if error > 0:
        current_sign = 1
    elif error < 0:
        current_sign = -1
    else:
        return 0, last_sign

    if last_sign != 0 and current_sign != last_sign:
        return 1, current_sign

    return 0, current_sign


# Utilities
def load_calibration(path):
    try:
        with open(path) as file:
            lines = file.readlines()

        values = lines[-1].strip().split(", ")

        return int(values[0]), int(values[1])

    except OSError:
        return BLACK_DEFAULT, WHITE_DEFAULT


def choose_controller_type():
    ev3.screen.clear()
    ev3.screen.print("ON_OFF: LEFT", "PROPORTIONAL: UP", "PID: RIGHT", sep="\n")

    pressed_buttons = []
    while True:
        pressed_buttons = ev3.buttons.pressed()

        if pressed_buttons and pressed_buttons[0] in (
            Button.LEFT,
            Button.UP,
            Button.RIGHT,
        ):
            chosen_button = pressed_buttons[0]
            break

    while ev3.buttons.pressed():
        pass

    ev3.screen.clear()

    if chosen_button == Button.LEFT:
        return ControllerType.ON_OFF
    elif chosen_button == Button.UP:
        return ControllerType.PROPORTIONAL
    elif chosen_button == Button.RIGHT:
        return ControllerType.PID


# Program

controller_type = choose_controller_type()

black, white = load_calibration("path/to/calibration")
sensor_threshold = (black + white) / 2

motor_left.reset_angle(0)
motor_right.reset_angle(0)

wait(START_DELAY)

watch.reset()
previous_time = watch.time()

while watch.time() < MAX_TIME:
    ...  # Main loop
