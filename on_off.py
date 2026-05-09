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
	"Tempo",
	"Distância",
	"Refletância",
	"Erro",
	"Velocidade Esq.",
	"Velocidade Dir.",
	"Velocidade Média",
	"Oscilação",
	"Suavidade",
	name="on_off",
	append=True
	)

watch = StopWatch()

# Variables

# Sensor
black = 8 									# Calibração do preto (%)
white = 80 									# Calibração do branco (%)
sensor_threshold = (black + white) / 2		# Calibração da média (%)
sensor_value = 0 							# Refletância (%)
sensor_error = 0 							# Erro (%)

# Motor
speed_base = 200 							# Valor experimental (deg/s)
speed_correction = 80 						# Valor experimental (deg/s)

# Roda
wheel_diameter = 56 						# (mm)
wheel_circumference = pi * wheel_diameter

# Direção
current_direction = None
last_direction = None

# Métricas
distance = 0
turns = 0
smoothness = 0

# Velocidades anteriores
previous_left_speed = 0
previous_right_speed = 0

# Program
watch.reset()

motor_left.reset_angle(0)
motor_right.reset_angle(0)

while color_sensor.color() != Color.RED:
	sensor_value = color_sensor.reflection()
	sensor_error = sensor_value - sensor_threshold

	# Controlador ON/OFF
	if sensor_value < sensor_threshold:
		current_direction = "RIGHT"

		motor_left.run(speed_base)
		motor_right.run(speed_base - speed_correction)

	else:
		current_direction = "LEFT"

		motor_left.run(speed_base - speed_correction)
		motor_right.run(speed_base)

	# Oscilação
	if current_direction != last_direction:
		turns += 1
		last_direction = current_direction

	# Suavidade
	current_left_speed = motor_left.speed()
	current_right_speed = motor_right.speed()

	delta_left = abs(current_left_speed - previous_left_speed)
	delta_right = abs(current_right_speed - previous_right_speed)

	smoothness = delta_left + delta_right

	previous_left_speed = current_left_speed
	previous_right_speed = current_right_speed

	# Distância
	left_angle = motor_left.angle()
	right_angle = motor_right.angle()

	average_angle = (left_angle + right_angle) / 2

	distance = wheel_circumference * (average_angle / 360)

	# Tempo
	time = watch.time()

	# Velocidade Média
	average_speed = distance / time

	# Registro
	data.log(
		time,
		distance,
		sensor_value,
		sensor_error,
		motor_left.speed(),
		motor_right.speed(),
		average_speed,
		turns,
		smoothness
		)

	wait(10)

motor_left.stop()
motor_right.stop()
