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

# Sensor
black = 7.252604166666667 					# Calibracao do preto (%)
white = 80.19298245614037 					# Calibracao do branco (%)
sensor_threshold = (black + white) / 2		# Calibracao da media (%)
sensor_hysteresis = 10						# Banda morta para reduzir oscilacao (%)
sensor_value = 0 							# Refletancia (%)
sensor_error = 0 							# Erro (%)

# Motor
speed_base = 200 							# Valor experimental (deg/s)
speed_correction = 150						# Valor experimental (deg/s)

# Roda
wheel_diameter = 56 						# (mm)
wheel_circumference = pi * wheel_diameter

# Direcao
current_direction = None
last_direction = "LEFT"

# Métricas
distance = 0
turns = 0
smoothness = 0

# Velocidades anteriores
previous_left_speed = 0
previous_right_speed = 0

def get_direction(reflection_value, threshold, hysteresis, last_direction):
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
	average_angle = (left_angle + right_angle) / 2
	return (circumference * (average_angle / 360)) / 1000


def compute_average_speed(distance, elapsed):
	if elapsed > 0:
		return distance / elapsed
	return 0


# Program
watch.reset()

motor_left.reset_angle(0)
motor_right.reset_angle(0)

while color_sensor.color() != Color.RED:
	sensor_value = color_sensor.reflection()
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

	# Distância
	left_angle = motor_left.angle()
	right_angle = motor_right.angle()

	distance = compute_distance(left_angle, right_angle, wheel_circumference)

	# Tempo
	time = watch.time() / 1000

	# Velocidade Media
	average_speed = compute_average_speed(distance, time)

	# Registro
	data.log(
		time,
		distance,
		sensor_value,
		abs(sensor_error),
		motor_left.speed(),
		motor_right.speed(),
		average_speed,
		turns,
		smoothness
		)

	wait(10)

motor_left.stop()
motor_right.stop()
