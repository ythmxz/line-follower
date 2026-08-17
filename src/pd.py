#!/usr/bin/env pybricks-micropython

import os
from math import pi

from pybricks.ev3devices import ColorSensor, Motor
from pybricks.hubs import EV3Brick
from pybricks.parameters import Color, Port
from pybricks.tools import DataLog, StopWatch, wait

# Objects

ev3 = EV3Brick()
motor_left = Motor(Port.B)
motor_right = Motor(Port.C)
color_sensor = ColorSensor(Port.S1)

specs = DataLog(
    "Preto (%)",
    "Branco (%)",
    "Limite (%)",
    "Kp ((deg/s)/%)",
    "Kd (deg/%)",
    "Velocidade Base (deg/s)",
    name="logs/pd/specs/specs",
)

data = DataLog(
    "Tempo (s)",
    "Distância (m)",
    "Refletância (%)",
    "Erro (%)",
    "Derivada (%/s)",
    "Correção P (deg/s)",
    "Correção D (deg/s)",
    "Correção Total (deg/s)",
    "Velocidade Esq. (deg/s)",
    "Velocidade Dir. (deg/s)",
    "Velocidade Média (m/s)",
    "Oscilação",
    "Suavidade (deg/s)",
    name="logs/pd/pd",
)

watch = StopWatch()

# Variables

# Sensor
WHITE_DEFAULT = 80  # (%)
BLACK_DEFAULT = 8  # (%)
sensor_value = 0  # (%)
sensor_error = 0  # (%)

# Controlador PD
speed_base = 150  # (deg/s)
proportional_gain = 2.3  # Kp: (deg/s) por %
derivative_gain = 0.05  # Kd: deg por %

# Roda
wheel_diameter = 56  # (mm)
wheel_circumference = pi * wheel_diameter  # (mm)

# Estado do controlador
previous_error = 0
previous_time = 0
first_iteration = True

# Métricas
distance = 0  # (mm)
turns = 0
smoothness = 0
last_error_sign = 0
previous_left_speed = 0
previous_right_speed = 0


def load_calibration(path, default_white, default_black):
    """Lê branco e preto do arquivo de calibração.

    Retorna os valores padrões caso não seja possível acessar ou
    interpretar o arquivo.

    Args:
        path (str): Caminho para o arquivo de calibração.
        default_white (float): Valor padrão de branco (%).
        default_black (float): Valor padrão de preto (%).

    Returns:
        tuple: Valores de branco e preto em %.
    """
    try:
        with open(path) as file:
            lines = file.readlines()

        values = lines[-1].strip().split(", ")

        return float(values[0]), float(values[1])
    except Exception:
        return default_white, default_black


def apply_pd_control(
    error,
    previous_error,
    elapsed_time,
    base_speed,
    proportional_gain,
    derivative_gain,
):
    """Aplica o controlador proporcional-derivativo.

    A correção é calculada por:

        correção = Kp * erro + Kd * derivada_do_erro

    Args:
        error (float): Erro atual do sensor (%).
        previous_error (float): Erro da iteração anterior (%).
        elapsed_time (float): Intervalo entre amostras (s).
        base_speed (float): Velocidade base dos motores (deg/s).
        proportional_gain (float): Ganho proporcional ((deg/s)/%).
        derivative_gain (float): Ganho derivativo (deg/%).

    Returns:
        tuple: Derivada do erro, correção proporcional,
            correção derivativa e correção total.
    """
    if elapsed_time > 0:
        error_derivative = (error - previous_error) / elapsed_time
    else:
        error_derivative = 0

    proportional_correction = proportional_gain * error
    derivative_correction = derivative_gain * error_derivative

    total_correction = proportional_correction + derivative_correction

    motor_left.run(base_speed - total_correction)
    motor_right.run(base_speed + total_correction)

    return (
        error_derivative,
        proportional_correction,
        derivative_correction,
        total_correction,
    )


def compute_oscillation(error, last_sign):
    """Detecta cruzamentos do setpoint pelo sinal do erro.

    Args:
        error (float): Erro atual do sensor (%).
        last_sign (int): Sinal anterior do erro (-1, 0 ou 1).

    Returns:
        tuple: Evento de oscilação e sinal atual do erro.
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


def compute_smoothness(
    left_speed,
    right_speed,
    previous_left,
    previous_right,
):
    """Calcula a variação total das velocidades dos motores.

    Args:
        left_speed (float): Velocidade atual do motor esquerdo (deg/s).
        right_speed (float): Velocidade atual do motor direito (deg/s).
        previous_left (float): Velocidade anterior esquerda (deg/s).
        previous_right (float): Velocidade anterior direita (deg/s).

    Returns:
        float: Variação total das velocidades (deg/s).
    """
    delta_left = abs(left_speed - previous_left)
    delta_right = abs(right_speed - previous_right)

    return delta_left + delta_right


def compute_distance(left_angle, right_angle, circumference):
    """Calcula a distância percorrida pelo centro do robô.

    Args:
        left_angle (float): Ângulo do motor esquerdo (graus).
        right_angle (float): Ângulo do motor direito (graus).
        circumference (float): Circunferência da roda (mm).

    Returns:
        float: Distância percorrida (mm).
    """
    average_angle = (left_angle + right_angle) / 2

    return circumference * (average_angle / 360)


def compute_average_speed(distance, elapsed):
    """Calcula a velocidade média.

    Numericamente, mm/ms equivale a m/s.

    Args:
        distance (float): Distância percorrida (mm).
        elapsed (float): Tempo decorrido (ms).

    Returns:
        float: Velocidade média (m/s).
    """
    if elapsed > 0:
        return distance / elapsed

    return 0


white, black = load_calibration(
    "logs/calibration/calibration.txt",
    WHITE_DEFAULT,
    BLACK_DEFAULT,
)

sensor_threshold = (black + white) / 2

motor_left.reset_angle(0)
motor_right.reset_angle(0)

specs.log(
    black / 100,
    white / 100,
    sensor_threshold / 100,
    proportional_gain,
    derivative_gain,
    speed_base,
)

wait(3000)

watch.reset()
previous_time = watch.time()

# Program

while color_sensor.color() != Color.RED and watch.time() < 120000:
    sensor_value = color_sensor.reflection()

    if sensor_value is None:
        wait(10)
        continue

    current_time = watch.time()
    delta_time = (current_time - previous_time) / 1000  # ms -> s

    sensor_error = sensor_value - sensor_threshold

    # Evita uma derivada artificialmente alta na primeira amostra.
    if first_iteration:
        previous_error = sensor_error
        delta_time = 0
        first_iteration = False

    (
        error_derivative,
        proportional_correction,
        derivative_correction,
        total_correction,
    ) = apply_pd_control(
        sensor_error,
        previous_error,
        delta_time,
        speed_base,
        proportional_gain,
        derivative_gain,
    )

    # Oscilação
    oscillation_event, last_error_sign = compute_oscillation(
        sensor_error,
        last_error_sign,
    )
    turns += oscillation_event

    # Velocidades atuais
    current_left_speed = motor_left.speed()
    current_right_speed = motor_right.speed()

    # Suavidade
    smoothness = compute_smoothness(
        current_left_speed,
        current_right_speed,
        previous_left_speed,
        previous_right_speed,
    )

    previous_left_speed = current_left_speed
    previous_right_speed = current_right_speed

    # Distância
    left_angle = motor_left.angle()
    right_angle = motor_right.angle()

    distance = compute_distance(
        left_angle,
        right_angle,
        wheel_circumference,
    )

    # Velocidade média
    average_speed = compute_average_speed(
        distance,
        current_time,
    )

    # Registro
    data.log(
        current_time / 1000,  # ms -> s
        distance / 1000,  # mm -> m
        sensor_value / 100,  # % -> 0–1
        sensor_error / 100,  # % -> 0–1
        error_derivative,  # %/s
        proportional_correction,  # deg/s
        derivative_correction,  # deg/s
        total_correction,  # deg/s
        current_left_speed,  # deg/s
        current_right_speed,  # deg/s
        average_speed,  # m/s
        turns,
        smoothness,
    )

    previous_error = sensor_error
    previous_time = current_time

    wait(10)

motor_left.stop()
motor_right.stop()
os.sync()
