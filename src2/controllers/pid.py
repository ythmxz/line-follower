"""
PID controller for line follower.

Applies Proportional-Integral-Derivative correction to the sensor error.

    correction = Kp × error + Ki × integral + Kd × derivative

With Ki = 0, the controller behaves as PD.
"""


def compute(
    error,
    previous_error,
    integral,
    delta_time,
    base_speed,
    proportional_gain,
    integral_gain,
    derivative_gain,
):
    """
    Computes motor speeds with PID correction.

    Args:
        error (float): Current sensor error (%).
        previous_error (float): Error from the previous iteration (%).
        integral (float): Error integral accumulator (%·s).
        delta_time (float): Time between samples (s).
        base_speed (float): Base motor speed (deg/s).
        proportional_gain (float): Proportional gain ((deg/s)/%).
        integral_gain (float): Integral gain ((deg/s)/(%·s)).
        derivative_gain (float): Derivative gain ((deg/s)/(%/s)).

    Returns:
        tuple: (left_speed, right_speed, p_correction, i_correction,
                d_correction, total_correction, derivative, new_integral).
    """
    # Proportional
    p_correction = proportional_gain * error

    # Integral
    new_integral = integral + error * delta_time
    i_correction = integral_gain * new_integral

    # Derivative
    if delta_time > 0:
        derivative = (error - previous_error) / delta_time
    else:
        derivative = 0

    d_correction = derivative_gain * derivative

    # Total correction
    total_correction = p_correction + i_correction + d_correction

    left_speed = base_speed - total_correction
    right_speed = base_speed + total_correction

    return (
        left_speed,
        right_speed,
        p_correction,
        i_correction,
        d_correction,
        total_correction,
        derivative,
        new_integral,
    )
