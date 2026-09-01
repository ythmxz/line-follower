#!/usr/bin/env pybricks-micropython

"""
EV3 — Straight line test.

Lets the user pick a speed and duration, then drives straight.
"""

from pybricks.ev3devices import Motor
from pybricks.hubs import EV3Brick
from pybricks.parameters import Button, Port
from pybricks.tools import wait

# --- Hardware ---

ev3 = EV3Brick()
motor_left = Motor(Port.B)
motor_right = Motor(Port.C)

# --- Constants ---

DEBOUNCE_MS = 200
POLL_MS = 20

# --- Helpers ---


def _wait_release():
    while ev3.buttons.pressed():
        wait(POLL_MS)


def _wait_press_any():
    while not ev3.buttons.pressed():
        wait(POLL_MS)
    buttons = ev3.buttons.pressed()
    wait(DEBOUNCE_MS)
    _wait_release()
    return buttons


def pick_value(title, initial, step):
    """Shows a screen to adjust an integer value with UP/DOWN, confirm with CENTER."""
    current = initial

    while True:
        ev3.screen.clear()
        ev3.screen.print(title)
        ev3.screen.print("Valor: " + str(current))
        ev3.screen.print("^: + | v: - | O: Ok")

        buttons = _wait_press_any()

        if Button.UP in buttons:
            current += step
        elif Button.DOWN in buttons:
            current -= step
            if current < step:
                current = step
        elif Button.CENTER in buttons:
            return current


# --- Main ---

speed = pick_value("VELOCIDADE (deg/s)", 200, 10)
duration = pick_value("DURACAO (s)", 5, 1)

ev3.screen.clear()
ev3.screen.print("Vel: " + str(speed) + " deg/s")
ev3.screen.print("Tempo: " + str(duration) + " s")
ev3.screen.print("O: Iniciar")
ev3.screen.print("<: Cancelar")

while True:
    buttons = _wait_press_any()
    if Button.CENTER in buttons:
        break
    if Button.LEFT in buttons:
        raise SystemExit

motor_left.run(speed)
motor_right.run(speed)

wait(duration * 1000)

motor_left.stop()
motor_right.stop()

ev3.screen.clear()
ev3.screen.print("Concluido!")
wait(2000)
