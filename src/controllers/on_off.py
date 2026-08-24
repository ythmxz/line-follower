"""
ON/OFF controller for line follower.

Implements binary control with dead band (hysteresis).
When the sensor detects deviation beyond threshold ± hysteresis,
a fixed correction is applied by reducing one motor's speed.
"""


def get_direction(reflection, threshold, hysteresis, last_direction):
    """
    Determines the correction direction based on reflectance and hysteresis.

    Args:
        reflection (float): Reflectance read by the sensor (%).
        threshold (float): Controller setpoint (%).
        hysteresis (float): Dead band (%).
        last_direction (str): Last applied direction.

    Returns:
        str: "LEFT" or "RIGHT".
    """
    if reflection < (threshold - hysteresis):
        return "RIGHT"

    if reflection > (threshold + hysteresis):
        return "LEFT"

    return last_direction


def compute(direction, base_speed, correction):
    """
    Computes motor speeds with ON/OFF correction.

    Reduces one motor's speed by a fixed amount while keeping
    the other at base speed.

    Args:
        direction (str): Correction direction ("LEFT" or "RIGHT").
        base_speed (float): Base motor speed (deg/s).
        correction (float): Fixed speed correction (deg/s).

    Returns:
        tuple: (left_speed, right_speed) in deg/s.
    """
    if direction == "RIGHT":
        return base_speed, base_speed - correction

    return base_speed - correction, base_speed
