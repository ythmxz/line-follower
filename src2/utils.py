"""
Utility functions for the EV3 line follower.

Provides configuration loading, calibration reading, and shared
metric computations used across all controller types.
"""

import json

# --- Configuration ---


def load_config(path):
    """
    Loads configuration from a JSON file.

    Args:
        path (str): Path to the config.json file.

    Returns:
        dict: Dictionary with configuration parameters.
    """
    with open(path) as f:
        return json.load(f)


# --- Calibration ---


def load_calibration(path, default_white, default_black):
    """
    Reads white and black values from the calibration file.

    Falls back to the provided defaults if the file is missing or invalid.

    Args:
        path (str): Path to the calibration file.
        default_white (float): Default white value (%).
        default_black (float): Default black value (%).

    Returns:
        tuple: (white, black) in %.
    """
    try:
        with open(path) as f:
            lines = f.readlines()

        values = lines[-1].strip().split(", ")

        return float(values[0]), float(values[1])

    except Exception:
        return default_white, default_black


# --- Environment Metrics ---


def compute_distance(left_angle, right_angle, circumference):
    """
    Computes the distance traveled by the robot's center.

    Args:
        left_angle (float): Accumulated left motor angle (degrees).
        right_angle (float): Accumulated right motor angle (degrees).
        circumference (float): Wheel circumference (mm).

    Returns:
        float: Distance traveled (mm).
    """
    average_angle = (left_angle + right_angle) / 2

    return circumference * (average_angle / 360)


def compute_average_speed(distance, elapsed):
    """
    Computes the average speed.

    Numerically, mm/ms equals m/s.

    Args:
        distance (float): Distance traveled (mm).
        elapsed (float): Elapsed time (ms).

    Returns:
        float: Average speed (m/s).
    """
    if elapsed > 0:
        return distance / elapsed

    return 0


# --- Curve Metrics ---


def compute_smoothness(current_speed, previous_speed):
    """
    Computes the absolute speed variation for a single motor.

    Args:
        current_speed (float): Current motor speed (deg/s).
        previous_speed (float): Previous motor speed (deg/s).

    Returns:
        float: Absolute speed variation (deg/s).
    """
    return abs(current_speed - previous_speed)


def compute_oscillation(error, last_sign):
    """
    Detects setpoint crossings by tracking the error sign.

    Args:
        error (float): Current sensor error (%).
        last_sign (int): Error sign from the previous iteration (-1, 0, or 1).

    Returns:
        tuple: (event, current_sign) where event is 1 on crossing,
            0 otherwise.
    """
    if error > 0:
        current_sign = 1
    elif error < 0:
        current_sign = -1
    else:
        return 0, last_sign

    if last_sign != 0 and current_sign != last_sign:
        return 1, current_sign

    return 0, current_sign
