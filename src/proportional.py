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
# Kp não é uma medida em % — é um ganho (deg/s por %) que opera internamente
# na escala 0-100, por isso seu rótulo deixa isso explícito.
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
    "Erro (%)",           # Com sinal: positivo = branco, negativo = preto
    "Correção (deg/s)",     # Kp × erro — útil para analisar o controlador
    "Velocidade Esq. (deg/s)",
    "Velocidade Dir. (deg/s)",
    "Velocidade Média (m/s)",
    "Oscilação",
    "Suavidade (deg/s)",
    name="logs/proportional/proportional",
)

watch = StopWatch()

# Variables
# Sensor (escala 0-100, como retornado por color_sensor.reflection())
black = 75.00053149083179               # Calibração do preto (%)
white = 7.785390713476784               # Calibração do branco (%)
sensor_threshold = (black + white) / 2  # Setpoint do controlador (%)
sensor_value = 0                        # Refletância lida (%)
sensor_error = 0                        # Erro com sinal (%)

# Controlador P
speed_base = 210          # Velocidade base (deg/s)
proportional_gain = 2.0   # Ganho proporcional (deg/s por %)
                          # proportional_gain opera na escala 0-100: erro(%) × proportional_gain(deg/s por %)
                          # → correção em deg/s. Não se normaliza.
                          # Estimativa inicial: correction_on_off / (2 × erro_max)
                          # = 152 / (2 × 35.57) ≈ 2.14

# Roda — wheel_diameter em mm, portanto wheel_circumference também em mm.
# Isso garante que compute_distance() retorne mm, unidade bruta do sistema.
wheel_diameter = 56                         # (mm)
wheel_circumference = pi * wheel_diameter   # (mm)

# Métricas
distance = 0    # (mm) — convertido para m apenas no log
turns = 0
smoothness = 0
last_error_sign = 0     # Rastreia o sinal do erro para detectar oscilações

# Velocidades anteriores (para cálculo de suavidade)
previous_left_speed = 0
previous_right_speed = 0

def apply_p_control(error, base_speed, proportional_gain):
    # error em %, proportional_gain em deg/s por % → correction em deg/s. Tudo consistente.
    # erro > 0 (vendo branco): esq. freia, dir. acelera → vira à esquerda.
    # erro < 0 (vendo preto):  esq. acelera, dir. freia → vira à direita.
    # A velocidade média é preservada em base_speed, pois as correções se
    # aplicam simétricamente e em sentidos opostos nos dois motores.
    correction = proportional_gain * error
    left_speed = base_speed - correction
    right_speed = base_speed + correction
    motor_left.run(left_speed)
    motor_right.run(right_speed)
    return correction   # (deg/s) — retornado para registro no DataLog


def compute_oscillation(error, last_sign):
    # Detecta cruzamentos do setpoint (mudanças de sinal do erro).
    # Equivalente às trocas de direção LEFT/RIGHT do controlador ON/OFF.
    if error > 0:
        current_sign = 1
    elif error < 0:
        current_sign = -1
    else:
        # Erro exatamente zero: não define novo lado, mantém o anterior.
        return 0, last_sign

    if last_sign != 0 and current_sign != last_sign:
        return 1, current_sign  # Cruzamento detectado
    return 0, current_sign


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
# valores em % → 0-1 (÷ 100). proportional_gain e speed_base já estão em deg/s.
specs.log(
    black / 100,              # % → 0-1
    white / 100,              # % → 0-1
    sensor_threshold / 100,   # % → 0-1
    proportional_gain,        # deg/s por % — ganho do controlador, sem conversão
    speed_base,               # deg/s — sem conversão
)

wait(3000)
watch.reset()

while color_sensor.color() != Color.RED and watch.time() < 45000:
    sensor_value = color_sensor.reflection()

    if sensor_value is None:
        wait(10)
        continue

    # Erro na escala original (%) para alimentar corretamente apply_p_control(),
    # que usa proportional_gain calibrado nessa mesma escala (deg/s por %).
    sensor_error = sensor_value - sensor_threshold

    # Aplica o controlador P e captura a correção (deg/s) para o log.
    correction = apply_p_control(sensor_error, speed_base, proportional_gain)

    # Oscilação: conta cruzamentos do setpoint pelo sinal do erro.
    osc_event, last_error_sign = compute_oscillation(sensor_error, last_error_sign)
    turns += osc_event

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
        time / 1000,           # ms  → s
        distance / 1000,       # mm  → m
        sensor_value / 100,    # %   → 0-1
        sensor_error / 100,    # %   → 0-1  (com sinal, diferente do ON/OFF)
        correction,            # deg/s — sem conversão (Kp[deg/s por %] × erro[%])
        motor_left.speed(),    # deg/s — sem conversão
        motor_right.speed(),   # deg/s — sem conversão
        average_speed / 1000,  # mm/ms → m/s
        turns,                 # contador — sem conversão
        smoothness,            # deg/s — sem conversão
    )

    wait(10)

motor_left.stop()
motor_right.stop()
