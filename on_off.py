#!/usr/bin/env pybricks-micropython
from math import pi
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, ColorSensor)
from pybricks.parameters import (Port, Color)
from pybricks.tools import (DataLog, StopWatch, wait)

# Objects
ev3 = EV3Brick()

motor_left = Motor(Port.B)
motor_right = Motor(Port.C)
color_sensor = ColorSensor(Port.S1)

# Os cabeçalhos descrevem as unidades dos valores *após* a conversão no log.
specs = DataLog(
    "Preto (%)",
    "Branco (%)",
    "Limite (%)",
    "Banda Morta (%)",
    "Velocidade Base (deg/s)",
    "Correção (deg/s)",
    name="logs/on_off/specs/specs",
)

data = DataLog(
    "Tempo (s)",
    "Distância (m)",
    "Refletância (%)",
    "Erro (%)",
    "Velocidade Esq. (deg/s)",
    "Velocidade Dir. (deg/s)",
    "Velocidade Média (m/s)",
    "Oscilação",
    "Suavidade (deg/s)",
    name="logs/on_off/on_off",
)

watch = StopWatch()

# Variables
# Sensor (escala 0-100, como retornado por color_sensor.reflection())
black = 7.022368421052631               # Calibração do preto (%)
white = 78.15824915824916               # Calibração do branco (%)
sensor_threshold = (black + white) / 2  # Setpoint (%)
sensor_hysteresis = 3                   # Banda morta (%)
sensor_value = 0                        # Refletância lida (%)
sensor_error = 0                        # Erro (%)

# Motor
speed_base = 210        # Velocidade base (deg/s)
speed_correction = 152  # Correção fixa ON/OFF (deg/s)

# Roda — wheel_diameter em mm, portanto wheel_circumference também em mm.
# Isso garante que compute_distance() retorne mm, unidade bruta do sistema.
wheel_diameter = 56                         # (mm)
wheel_circumference = pi * wheel_diameter   # (mm)

# Direção
current_direction = None
last_direction = "LEFT"

# Métricas
distance = 0    # (mm) — convertido para m apenas no log
turns = 0
smoothness = 0

# Velocidades anteriores (para cálculo de suavidade)
previous_left_speed = 0
previous_right_speed = 0

def get_direction(reflection_value, threshold, hysteresis, last_direction):
    # Todas as comparações usam a escala original (0-100): correto.
    if reflection_value < (threshold - hysteresis):
        return "RIGHT"
    if reflection_value > (threshold + hysteresis):
        return "LEFT"
    return last_direction


def apply_on_off(direction, base_speed, correction):
    if direction == "RIGHT":
        motor_left.run(base_speed)
        motor_right.run(base_speed - correction)
    else:
        motor_left.run(base_speed - correction)
        motor_right.run(base_speed)


def compute_smoothness(left_speed, right_speed, prev_left, prev_right):
    delta_left = abs(left_speed - prev_left)
    delta_right = abs(right_speed - prev_right)
    return delta_left + delta_right


def compute_distance(left_angle, right_angle, circumference):
    # circumference está em mm, portanto o retorno também é mm.
    # A divisão por 1000 (mm → m) foi movida para o log.
    average_angle = (left_angle + right_angle) / 2
    return circumference * (average_angle / 360)    # (mm)


def compute_average_speed(distance, elapsed):
    # distance em mm, elapsed em ms.
    # Coincidência de escala: mm/ms = (10⁻³ m)/(10⁻³ s) = m/s.
    # O resultado já está em m/s sem nenhuma conversão adicional.
    if elapsed > 0:
        return distance / elapsed   # (m/s)
    return 0


# Program
motor_left.reset_angle(0)
motor_right.reset_angle(0)

# Conversões de apresentação concentradas aqui:
# valores em % → 0-1 (÷ 100). Velocidades já estão em deg/s.
specs.log(
    black / 100,               # % → 0-1
    white / 100,               # % → 0-1
    sensor_threshold / 100,    # % → 0-1
    sensor_hysteresis / 100,   # % → 0-1
    speed_base,                # deg/s — sem conversão
    speed_correction,          # deg/s — sem conversão
)

wait(3000)
watch.reset()

while color_sensor.color() != Color.RED and watch.time() < 120000:
    sensor_value = color_sensor.reflection()

    if sensor_value is None:
        wait(10)
        continue

    # Erro na escala original (%) para alimentar corretamente get_direction(),
    # que compara com threshold e hysteresis também em %.
    sensor_error = sensor_value - sensor_threshold

    current_direction = get_direction(
        sensor_value,
        sensor_threshold,
        sensor_hysteresis,
        last_direction,
    )
    apply_on_off(current_direction, speed_base, speed_correction)

    # Oscilação
    if current_direction != last_direction:
        turns += 1
        last_direction = current_direction

    # Suavidade
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

    # Distância em mm — wheel_circumference está em mm, portanto correto.
    left_angle = motor_left.angle()
    right_angle = motor_right.angle()
    distance = compute_distance(left_angle, right_angle, wheel_circumference)

    # Tempo em ms — unidade bruta do StopWatch. A divisão por 1000 foi
    # movida para o log.
    time = watch.time()     # (ms)

    # Velocidade média: distance(mm) / time(ms) = m/s.
    average_speed = compute_average_speed(distance, time)

    # ---------- Camada de apresentação — todas as conversões aqui ----------
    # Regra geral:
    #   ms  → s   (÷ 1000)
    #   mm  → m   (÷ 1000)
    #   %   → 0-1 (÷ 100)
    # Grandezas já em unidades finais (deg/s, m/s, contadores): sem conversão.
    data.log(
        time / 1000,              # ms  → s
        distance / 1000,          # mm  → m
        sensor_value / 100,       # %   → 0-1
        abs(sensor_error) / 100,  # %   → 0-1
        motor_left.speed(),       # deg/s — sem conversão
        motor_right.speed(),      # deg/s — sem conversão
        average_speed / 1000,     # mm/ms → m/s
        turns,                    # contador — sem conversão
        smoothness,               # deg/s — sem conversão
    )

    wait(10)

motor_left.stop()
motor_right.stop()
