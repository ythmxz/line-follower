"""
Proportional controller for line follower.

Applies proportional correction to the sensor error.

    correction = Kp × error

Positive error (seeing white): left slows, right speeds up → turns left.
Negative error (seeing black): left speeds up, right slows → turns right.
"""


def compute(error, base_speed, proportional_gain):
    """
    Computes motor speeds with proportional correction.

    Args:
        error (float): Sensor error relative to the setpoint (%).
        base_speed (float): Base motor speed (deg/s).
        proportional_gain (float): Proportional gain ((deg/s)/%).

    Returns:
        tuple: (left_speed, right_speed, correction) in deg/s.
    """
    correction = proportional_gain * error

    left_speed = base_speed - correction
    right_speed = base_speed + correction

    return left_speed, right_speed, correction
