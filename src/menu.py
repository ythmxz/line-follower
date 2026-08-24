#!/usr/bin/env pybricks-micropython

"""
EV3 Line Follower — Menu System.

Provides an interactive menu flow for configuring and starting a test run:
    1. Calibration screen  — calibrate, reuse existing, or use defaults.
    2. Controller screen   — choose ON/OFF, Proportional, or PID.
    3. Parameters screen   — tune each controller parameter one by one.
    4. Start screen        — confirm to run or cancel to exit.

Public API (intended for main.py):
    run_menu(ev3, color_sensor, config) -> (controller_type, params, white, black)
"""

from pybricks.ev3devices import ColorSensor
from pybricks.hubs import EV3Brick
from pybricks.parameters import Button, Port
from pybricks.tools import DataLog, wait

# =====================================================================
# Constants
# =====================================================================

ev3 = EV3Brick()
sensor = ColorSensor(Port.S1)

DEBOUNCE_MS = 200  # ms to wait after a button press to avoid double-reads
POLL_MS = 20  # polling interval inside wait loops

# Maps controller type strings to display labels
CONTROLLER_LABELS = {
    "on_off": "ON/OFF",
    "proportional": "Proporcional",
    "pid": "PID",
}

# Parameter definitions per controller.
# Each entry: (key, display_label, step, is_float)
CONTROLLER_PARAMS = {
    "on_off": [
        ("base_speed", "Vel. Base (deg/s)", 5, False),
        ("correction", "Correcao (deg/s)", 5, False),
        ("hysteresis", "Banda Morta (%)", 1, False),
    ],
    "proportional": [
        ("base_speed", "Vel. Base (deg/s)", 5, False),
        ("kp", "Kp ((deg/s)/%)", 0.1, True),
    ],
    "pid": [
        ("base_speed", "Vel. Base (deg/s)", 5, False),
        ("kp", "Kp ((deg/s)/%)", 0.1, True),
        ("ki", "Ki ((deg/s)/(%*s))", 0.1, True),
        ("kd", "Kd ((deg/s)/(%/s))", 0.05, True),
    ],
}

# =====================================================================
# Internal helpers
# =====================================================================


def _wait_release(ev3):
    """Blocks until all buttons are released."""
    while ev3.buttons.pressed():
        wait(POLL_MS)


def _wait_press_any(ev3):
    """Blocks until any button is pressed. Returns the set of buttons."""
    while not ev3.buttons.pressed():
        wait(POLL_MS)
    buttons = ev3.buttons.pressed()
    wait(DEBOUNCE_MS)
    _wait_release(ev3)
    return buttons


def _wait_center_release(ev3):
    """Blocks until the CENTER button is released (mirrors calibration.py)."""
    while Button.CENTER in ev3.buttons.pressed():
        wait(POLL_MS)


def _wait_center_press(ev3):
    """Blocks until the CENTER button is pressed (mirrors calibration.py)."""
    while Button.CENTER not in ev3.buttons.pressed():
        wait(POLL_MS)


def _sample_until_center(ev3, color_sensor):
    """Samples reflectance until CENTER is pressed (mirrors calibration.py).

    Returns:
        list: Reflectance values collected (%).
    """
    values = []
    while Button.CENTER not in ev3.buttons.pressed():
        values.append(color_sensor.reflection())
        wait(POLL_MS)
    return values


def _round_float(value, decimals):
    """Rounds a float to *decimals* decimal places (MicroPython-safe)."""
    factor = 10**decimals
    return int(value * factor + 0.5) / factor


def _format_float(value):
    """Returns a compact 2-decimal string for a float (avoids f-strings)."""
    sign = "-" if value < 0 else ""
    abs_val = abs(value)
    integer_part = int(abs_val)
    frac_part = int(_round_float(abs_val - integer_part, 2) * 100 + 0.5)
    if frac_part >= 100:
        integer_part += 1
        frac_part = 0
    return sign + str(integer_part) + "." + "{:02d}".format(frac_part)


def _format_value(value, is_float):
    """Returns a display string for an int or float parameter value."""
    if is_float:
        return _format_float(value)
    return str(int(value))


# =====================================================================
# Screen 1 — Calibration
# =====================================================================
# Options (UP/DOWN to scroll, CENTER to select):
#   > Calibrar
#     Usar atual
#     Usar padrao


def calibration_screen(
    ev3, color_sensor, calibration_path, default_white, default_black
):
    """
    Displays the calibration menu.

    Args:
        ev3 (EV3Brick): EV3 brick instance.
        color_sensor (ColorSensor): Color sensor instance.
        calibration_path (str): Path to the calibration file.
        default_white (float): Default white reflectance (%).
        default_black (float): Default black reflectance (%).

    Returns:
        tuple: (white, black) reflectance values (%).
    """
    options = ["Calibrar", "Usar atual", "Usar padrao"]
    selected = 0

    while True:
        ev3.screen.clear()
        ev3.screen.print("CALIBRACAO")
        for i, label in enumerate(options):
            prefix = "> " if i == selected else "  "
            ev3.screen.print(prefix + label)

        buttons = _wait_press_any(ev3)

        if Button.UP in buttons:
            selected = (selected - 1) % len(options)
        elif Button.DOWN in buttons:
            selected = (selected + 1) % len(options)
        elif Button.CENTER in buttons:
            break

    # --- Calibrar ---
    if selected == 0:
        data = DataLog(
            "Branco",
            "Preto",
            name="logs/calibration/calibration",
            timestamp=False,
            extension="txt",
        )

        # --- White ---
        ev3.screen.clear()
        ev3.screen.print("Posicione sobre")
        ev3.screen.print("o BRANCO e")
        ev3.screen.print("pressione CENTER.")

        _wait_center_release(ev3)
        _wait_center_press(ev3)
        _wait_center_release(ev3)
        ev3.speaker.beep()

        ev3.screen.clear()
        ev3.screen.print("Amostrando BRANCO")
        ev3.screen.print("Pressione CENTER")
        ev3.screen.print("para confirmar.")

        white_values = _sample_until_center(ev3, color_sensor)
        white = sum(white_values) / len(white_values) if white_values else default_white
        ev3.speaker.beep()

        # --- Black ---
        ev3.screen.clear()
        ev3.screen.print("Posicione sobre")
        ev3.screen.print("o PRETO e")
        ev3.screen.print("pressione CENTER.")

        _wait_center_release(ev3)
        _wait_center_press(ev3)
        _wait_center_release(ev3)
        ev3.speaker.beep()

        ev3.screen.clear()
        ev3.screen.print("Amostrando PRETO")
        ev3.screen.print("Pressione CENTER")
        ev3.screen.print("para confirmar.")

        black_values = _sample_until_center(ev3, color_sensor)
        black = sum(black_values) / len(black_values) if black_values else default_black
        ev3.speaker.beep()

        data.log(white, black)

        ev3.screen.clear()
        ev3.screen.print("Calibrado!")
        ev3.screen.print("Branco: " + _format_float(white))
        ev3.screen.print("Preto:  " + _format_float(black))
        wait(2000)

        return white, black

    # --- Usar atual ---
    if selected == 1:
        try:
            with open(calibration_path) as f:
                lines = f.readlines()
            values = lines[-1].strip().split(", ")
            white = float(values[0])
            black = float(values[1])

            ev3.screen.clear()
            ev3.screen.print("Calibracao atual:")
            ev3.screen.print("Branco: " + _format_float(white))
            ev3.screen.print("Preto:  " + _format_float(black))
            wait(2000)

            return white, black

        except Exception:
            ev3.screen.clear()
            ev3.screen.print("Sem calibracao!")
            ev3.screen.print("Usando padrao.")
            wait(2000)
            return default_white, default_black

    # --- Usar padrao ---
    ev3.screen.clear()
    ev3.screen.print("Usando padrao:")
    ev3.screen.print("Branco: " + _format_float(default_white))
    ev3.screen.print("Preto:  " + _format_float(default_black))
    wait(2000)

    return default_white, default_black


# =====================================================================
# Screen 2 — Controller selection
# =====================================================================


def controller_screen(ev3):
    """
    Displays the controller selection menu.

    Args:
        ev3 (EV3Brick): EV3 brick instance.

    Returns:
        str: Selected controller type key ("on_off", "proportional", "pid").
    """
    keys = ["on_off", "proportional", "pid"]
    selected = 0

    while True:
        ev3.screen.clear()
        ev3.screen.print("CONTROLADOR")
        for i, key in enumerate(keys):
            prefix = "> " if i == selected else "  "
            ev3.screen.print(prefix + CONTROLLER_LABELS[key])

        buttons = _wait_press_any(ev3)

        if Button.UP in buttons:
            selected = (selected - 1) % len(keys)
        elif Button.DOWN in buttons:
            selected = (selected + 1) % len(keys)
        elif Button.CENTER in buttons:
            return keys[selected]


# =====================================================================
# Screen 3 — Parameter tuning
# =====================================================================
# For each parameter:
#   Line 1: "=== Parametros ==="
#   Line 2: "<display_label>"
#   Line 3: "Orig: <original_value>"
#   Line 4: "Atual: <current_value>"
#   Line 5: "^ aum  v dim  O ok"


def parameters_screen(ev3, controller_type, config):
    """
    Displays the parameter adjustment screen for each controller parameter.

    Args:
        ev3 (EV3Brick): EV3 brick instance.
        controller_type (str): Controller type key.
        config (dict): Full config dict (used to seed current values).

    Returns:
        dict: Updated parameter dict for the selected controller.
    """
    param_defs = CONTROLLER_PARAMS[controller_type]
    base_cfg = config[controller_type]

    # Work on a mutable copy seeded from config
    params = {}
    for key, _label, _step, _is_float in param_defs:
        params[key] = base_cfg[key]

    for key, label, step, is_float in param_defs:
        original = params[key]
        current = original

        while True:
            ev3.screen.clear()
            ev3.screen.print("PARAMETROS")
            ev3.screen.print(label)
            ev3.screen.print("ORIG.: " + _format_value(original, is_float))
            ev3.screen.print("ATUAL: " + _format_value(current, is_float))
            ev3.screen.print("^: + | v: - | O: Ok")

            buttons = _wait_press_any(ev3)

            if Button.UP in buttons:
                current = current + step
                if is_float:
                    decimals = 2 if step < 0.1 else 1
                    current = _round_float(current, decimals)
            elif Button.DOWN in buttons:
                current = current - step
                if is_float:
                    decimals = 2 if step < 0.1 else 1
                    current = _round_float(current, decimals)
            elif Button.CENTER in buttons:
                params[key] = current
                break

    return params


# =====================================================================
# Screen 4 — Start / Cancel
# =====================================================================


def start_screen(ev3, controller_type, params):
    """
    Displays the start confirmation screen.

    Shows the chosen controller and key parameters, then waits for
    CENTER (start) or LEFT (cancel).

    Args:
        ev3 (EV3Brick): EV3 brick instance.
        controller_type (str): Controller type key.
        params (dict): Parameter dict for the controller.

    Returns:
        bool: True if the user confirmed start, False if cancelled.
    """
    while True:
        ev3.screen.clear()
        ev3.screen.print("INICIO")
        ev3.screen.print(CONTROLLER_LABELS[controller_type])
        ev3.screen.print("Vel: " + str(int(params["base_speed"])))
        ev3.screen.print("O: Iniciar")
        ev3.screen.print("<: Cancelar")

        buttons = _wait_press_any(ev3)

        if Button.CENTER in buttons:
            return True
        if Button.LEFT in buttons:
            return False


# =====================================================================
# Public entry point
# =====================================================================


def run_menu(ev3, color_sensor, config):
    """
    Runs the full menu flow and returns all values needed to start a test.

    Flow:
        calibration_screen -> controller_screen -> parameters_screen
        -> start_screen (loops back to controller_screen on cancel)

    Args:
        ev3 (EV3Brick): EV3 brick instance.
        color_sensor (ColorSensor): Color sensor instance.
        config (dict): Full configuration dict (from config.json).

    Returns:
        tuple: (controller_type, params, white, black)
            controller_type (str): "on_off", "proportional", or "pid".
            params (dict): Tuned parameter dict for the controller.
            white (float): White reflectance calibration value (%).
            black (float): Black reflectance calibration value (%).
    """
    # Step 1: Calibration (runs once at the start)
    white, black = calibration_screen(
        ev3,
        color_sensor,
        config["sensor"]["calibration_path"],
        config["sensor"]["white_default"],
        config["sensor"]["black_default"],
    )

    while True:
        # Step 2: Controller selection
        controller_type = controller_screen(ev3)

        # Step 3: Parameter tuning
        params = parameters_screen(ev3, controller_type, config)

        # Step 4: Start confirmation
        confirmed = start_screen(ev3, controller_type, params)

        if confirmed:
            return controller_type, params, white, black

        # Cancelled — terminate the program
        raise SystemExit
