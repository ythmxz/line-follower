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
    "Velocidade Base (deg/s)",
    name="logs/proportional/specs/specs",
)

data = DataLog(
    "Tempo (s)",
    "Distância (m)",
    "Refletância (%)",
    "Erro (%)",
    "Correção (deg/s)",
    "Velocidade Esq. (deg/s)",
    "Velocidade Dir. (deg/s)",
    "Velocidade Média (m/s)",
    "Oscilação",
    "Suavidade (deg/s)",
    name="logs/proportional/proportional",
)

watch = StopWatch()

# Variables

# Sensor
WHITE_DEFAULT = 80  # (%)
BLACK_DEFAULT = 8  # (%)
sensor_value = 0  # (%)
sensor_error = 0  # (%)

# Controlador P
speed_base = 150  # (deg/s)
proportional_gain = 2.3  # (deg/s por %)

# Roda
wheel_diameter = 56  # (mm)
wheel_circumference = pi * wheel_diameter  # (mm)

# Estado
distance = 0  # (mm)
turns = 0
smoothness = 0
last_error_sign = 0
previous_left_speed = 0
previous_right_speed = 0


def load_calibration(path, default_white, default_black):
    """Lê branco e preto do arquivo de calibração; retorna os padrões em caso de falha.

    Args:
        path (str): Caminho para o arquivo de calibração.
        default_white (float): Valor padrão de branco (%).
        default_black (float): Valor padrão de preto (%).

    Returns:
        tuple: (white, black) em %.
    """
    try:
        with open(path) as f:
            lines = f.readlines()

        values = lines[-1].strip().split(", ")

        return float(values[0]), float(values[1])
    except Exception:
        return default_white, default_black


def apply_p_control(error, base_speed, gain):
    """Aplica correção proporcional e aciona os motores.

    Erro positivo (vendo branco): esq. freia, dir. acelera -> vira à esquerda.
    Erro negativo (vendo preto):  esq. acelera, dir. freia -> vira à direita.

    Args:
        error (float): Erro do sensor em relação ao setpoint (%).
        base_speed (float): Velocidade base dos motores (deg/s).
        gain (float): Ganho proporcional (deg/s por %).

    Returns:
        float: Correção aplicada (deg/s).
    """
    correction = gain * error
    motor_left.run(base_speed - correction)
    motor_right.run(base_speed + correction)

    return correction


def compute_oscillation(error, last_sign):
    """Detecta cruzamentos do setpoint pelo sinal do erro.

    Args:
        error (float): Erro atual do sensor (%).
        last_sign (int): Sinal do erro na iteração anterior (-1, 0 ou 1).

    Returns:
        tuple: (evento, sinal_atual) onde evento vale 1 no cruzamento, 0 caso contrário.
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


def compute_smoothness(left_speed, right_speed, prev_left, prev_right):
    """Retorna a soma das variações absolutas de velocidade como métrica de suavidade.

    Args:
        left_speed (float): Velocidade atual do motor esquerdo (deg/s).
        right_speed (float): Velocidade atual do motor direito (deg/s).
        prev_left (float): Velocidade anterior do motor esquerdo (deg/s).
        prev_right (float): Velocidade anterior do motor direito (deg/s).

    Returns:
        float: Variação total de velocidade (deg/s).
    """
    return abs(left_speed - prev_left) + abs(right_speed - prev_right)


def compute_distance(left_angle, right_angle, circumference):
    """Retorna a distância percorrida com base no ângulo médio das rodas.

    Args:
        left_angle (float): Ângulo acumulado do motor esquerdo (graus).
        right_angle (float): Ângulo acumulado do motor direito (graus).
        circumference (float): Circunferência da roda (mm).

    Returns:
        float: Distância percorrida (mm).
    """
    average_angle = (left_angle + right_angle) / 2

    return circumference * (average_angle / 360)


def compute_average_speed(distance, elapsed):
    """Retorna a velocidade média dados distância em mm e tempo em ms.

    mm/ms == m/s por coincidência de escala: (1e-3 m)/(1e-3 s) = 1 m/s.

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
    "logs/calibration/calibration.txt", WHITE_DEFAULT, BLACK_DEFAULT
)
sensor_threshold = (black + white) / 2

motor_left.reset_angle(0)
motor_right.reset_angle(0)

specs.log(
    black / 100,
    white / 100,
    sensor_threshold / 100,
    proportional_gain,
    speed_base,
)

wait(3000)
watch.reset()

# Program

while color_sensor.color() != Color.RED and watch.time() < 120000:
    sensor_value = color_sensor.reflection()

    if sensor_value is None:
        wait(10)
        continue

    sensor_error = sensor_value - sensor_threshold
    correction = apply_p_control(sensor_error, speed_base, proportional_gain)

    osc_event, last_error_sign = compute_oscillation(sensor_error, last_error_sign)
    turns += osc_event

    current_left_speed = motor_left.speed()
    current_right_speed = motor_right.speed()
    smoothness = compute_smoothness(
        current_left_speed,
        current_right_speed,
        previous_left_speed,
        previous_right_speed,
    )
    previous_left_speed = current_left_speed
    previous_right_speed = current_right_speed

    left_angle = motor_left.angle()
    right_angle = motor_right.angle()
    distance = compute_distance(left_angle, right_angle, wheel_circumference)

    time = watch.time()
    average_speed = compute_average_speed(distance, time)

    data.log(
        time / 1000,  # ms  -> s
        distance / 1000,  # mm  -> m
        sensor_value / 100,  # %   -> 0-1
        sensor_error / 100,  # %   -> 0-1
        correction,
        motor_left.speed(),
        motor_right.speed(),
        average_speed / 1000,  # mm/ms -> m/s
        turns,
        smoothness,
    )

    wait(10)

motor_left.stop()
motor_right.stop()
os.sync()
