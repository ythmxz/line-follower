#!/usr/bin/env pybricks-micropython

"""
EV3 Line Follower — Main Script.

Execution flow:
    1. Loads configuration from config.json
    2. Initializes hardware (EV3, motors, color sensor)
    3. Loads sensor calibration
    5. Runs the control loop
    6. Logs data to CSV file
    7. Stops motors and syncs filesystem
"""

from math import pi

from pybricks.ev3devices import ColorSensor, Motor
from pybricks.hubs import EV3Brick
from pybricks.parameters import Color, Port
from pybricks.tools import DataLog, StopWatch, wait

from controllers import on_off, pid, proportional
from menu import run_menu
from utils import (
    compute_average_speed,
    compute_distance,
    compute_oscillation,
    compute_smoothness,
    load_config,
)

# --- Enumerations ---


class ControllerType:
    """Available controller types."""

    ON_OFF = "on_off"
    PROPORTIONAL = "proportional"
    PID = "pid"


# --- Constants ---

WHEEL_DIAMETER_MM = 56

# =====================================================================
# Main Program
# =====================================================================

# --- Hardware ---

ev3 = EV3Brick()
motor_left = Motor(Port.B)
motor_right = Motor(Port.C)
color_sensor = ColorSensor(Port.S1)
watch = StopWatch()

# --- Configuration ---

config = load_config("config.json")

# --- Menu / Controller selection ---

controller_type, controller_config, white, black = run_menu(ev3, color_sensor, config)
sensor_threshold = (black + white) / 2

# --- Gain variables for logging (set per controller type) ---

base_speed = controller_config["base_speed"]

if controller_type == ControllerType.ON_OFF:
    proportional_gain = 0
    integral_gain = 0
    derivative_gain = 0
elif controller_type == ControllerType.PROPORTIONAL:
    proportional_gain = controller_config["kp"]
    integral_gain = 0
    derivative_gain = 0
elif controller_type == ControllerType.PID:
    proportional_gain = controller_config["kp"]
    integral_gain = controller_config["ki"]
    derivative_gain = controller_config["kd"]

# --- DataLog ---

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
    "Correção P (°/s)",
    "Correção I (°/s)",
    "Correção D (°/s)",
    "Correção (°/s)",
    "Vel. Angular Esq. (°/s)",
    "Vel. Angular Dir. (°/s)",
    # Curves
    "Suavidade Esq. (°/s)",
    "Suavidade Dir. (°/s)",
    "Oscilação",
    name="logs/{}/data".format(controller_type),
)

# --- Derived constants ---

wheel_circumference = pi * WHEEL_DIAMETER_MM

# --- Shared state ---

turns = 0
last_error_sign = 0
previous_left_speed = 0
previous_right_speed = 0

# --- PID state ---

previous_error = 0
integral = 0
first_iteration = True

# --- ON/OFF state ---

last_direction = "LEFT"

# --- Timers ---

start_delay = config["timers"]["start_delay_ms"]
loop_delay = config["timers"]["loop_delay_ms"]
max_time = config["timers"]["max_time_ms"]

# --- Initialization ---

motor_left.reset_angle(0)
motor_right.reset_angle(0)

wait(start_delay)

watch.reset()
previous_time = watch.time()

# =====================================================================
# Main Loop
# =====================================================================

while color_sensor.color() != Color.RED and watch.time() < max_time:
    sensor_value = color_sensor.reflection()

    if sensor_value is None:
        wait(loop_delay)
        continue

    current_time = watch.time()
    delta_time = (current_time - previous_time) / 1000  # ms -> s

    sensor_error = sensor_value - sensor_threshold

    # Default correction values for logging
    p_correction = 0
    i_correction = 0
    d_correction = 0
    total_correction = 0
    left_speed = base_speed
    right_speed = base_speed

    # --- ON/OFF Control ---

    if controller_type == ControllerType.ON_OFF:
        direction = on_off.get_direction(
            sensor_value,
            sensor_threshold,
            controller_config["hysteresis"],
            last_direction,
        )

        left_speed, right_speed = on_off.compute(
            direction,
            base_speed,
            controller_config["correction"],
        )

        # Correction sign for log consistency:
        # positive -> turns left, negative -> turns right
        total_correction = controller_config["correction"]
        if direction == "RIGHT":
            total_correction = -total_correction

        if direction != last_direction:
            turns += 1
            last_direction = direction

    # --- Proportional Control ---

    elif controller_type == ControllerType.PROPORTIONAL:
        left_speed, right_speed, correction = proportional.compute(
            sensor_error,
            base_speed,
            proportional_gain,
        )

        p_correction = correction
        total_correction = correction

        osc_event, last_error_sign = compute_oscillation(sensor_error, last_error_sign)
        turns += osc_event

    # --- PID Control ---

    elif controller_type == ControllerType.PID:
        # Avoids artificially high derivative on the first sample
        if first_iteration:
            previous_error = sensor_error
            delta_time = 0
            first_iteration = False

        (
            left_speed,
            right_speed,
            p_correction,
            i_correction,
            d_correction,
            total_correction,
            _derivative,
            integral,
        ) = pid.compute(
            sensor_error,
            previous_error,
            integral,
            delta_time,
            base_speed,
            proportional_gain,
            integral_gain,
            derivative_gain,
        )

        osc_event, last_error_sign = compute_oscillation(sensor_error, last_error_sign)
        turns += osc_event

    # --- Motor actuation ---

    motor_left.run(left_speed)
    motor_right.run(right_speed)

    # --- Metrics ---

    current_left_speed = motor_left.speed()
    current_right_speed = motor_right.speed()

    left_smoothness = compute_smoothness(current_left_speed, previous_left_speed)
    right_smoothness = compute_smoothness(current_right_speed, previous_right_speed)

    distance = compute_distance(
        motor_left.angle(),
        motor_right.angle(),
        wheel_circumference,
    )

    average_speed = compute_average_speed(distance, current_time)

    # --- Logging ---

    data.log(
        # Environment
        current_time / 1000,  # ms -> s
        distance / 1000,  # mm -> m
        average_speed,  # m/s
        # Sensor
        black / 100,  # % -> 0-1
        white / 100,  # % -> 0-1
        sensor_threshold / 100,  # % -> 0-1
        sensor_value / 100,  # % -> 0-1
        sensor_error / 100,  # % -> 0-1
        # Control
        proportional_gain,  # (deg/s)/%
        integral_gain,  # (deg/s)/%
        derivative_gain,  # (deg/s)/%
        # Speed
        base_speed,  # deg/s
        p_correction,  # deg/s
        i_correction,  # deg/s
        d_correction,  # deg/s
        total_correction,  # deg/s
        current_left_speed,  # deg/s
        current_right_speed,  # deg/s
        # Curves
        left_smoothness,  # deg/s
        right_smoothness,  # deg/s
        turns,
    )

    # --- State update ---

    previous_left_speed = current_left_speed
    previous_right_speed = current_right_speed
    previous_error = sensor_error
    previous_time = current_time

    wait(loop_delay)

# =====================================================================
# Shutdown
# =====================================================================

motor_left.stop()
motor_right.stop()
