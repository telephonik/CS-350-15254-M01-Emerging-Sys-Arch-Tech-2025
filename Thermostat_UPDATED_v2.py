#
# Thermostat.py
#
# This is the Python code used to demonstrate the functionality of the
# thermostat prototype for CS 350.
#
# Hardware used:
# - AHT20 temperature sensor (I2C)
# - 16x2 LCD (GPIO)
# - Red LED (PWM via GPIO) for heating indicator
# - Blue LED (PWM via GPIO) for cooling indicator
# - Buttons (GPIO interrupts via gpiozero Button callbacks)
#
# Functional requirements implemented:
# - Three states: off, heat, cool
# - MODE button cycles: off -> heat -> cool -> off
# - Hardware constraint: only TWO buttons are used.
#     * MODE button (GPIO25): cycles the state
#     * SET button  (GPIO12): short press increases setPoint (+1°F)
#                             long press decreases setPoint (-1°F)
# - LED behavior:
#   * off: both LEDs off
#   * heat:
#       - if currentTemp < setPoint: red fades in/out
#       - else (>=): red solid on
#   * cool:
#       - if currentTemp > setPoint: blue fades in/out
#       - else (<=): blue solid on
# - LCD:
#   * line 1 shows date/time
#   * line 2 alternates between current temperature and state + setPoint
# - UART:
#   * every 30 seconds send: state,currentTemp,setPoint (comma delimited)
#
from time import sleep, monotonic
from datetime import datetime
from math import floor
from threading import Thread, Lock

from statemachine import StateMachine, State

import board
import adafruit_ahtx0

import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

import serial

from gpiozero import Button, PWMLED


DEBUG = True


# I2C and temperature sensor (AHT20/AHTx0 family)
i2c = board.I2C()
thSensor = adafruit_ahtx0.AHTx0(i2c)

# UART setup (Raspberry Pi UART)
ser = serial.Serial(
    port="/dev/ttyS0",       # /dev/ttyAMA0 prior to Raspberry Pi 3 in some setups
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1,
)

# LEDs (PWM)
redLight = PWMLED(18)
blueLight = PWMLED(23)


class ManagedDisplay:
    """Simple manager for a 16x2 LCD."""

    def __init__(self):
        self.lcd_rs = digitalio.DigitalInOut(board.D17)
        self.lcd_en = digitalio.DigitalInOut(board.D27)
        self.lcd_d4 = digitalio.DigitalInOut(board.D5)
        self.lcd_d5 = digitalio.DigitalInOut(board.D6)
        self.lcd_d6 = digitalio.DigitalInOut(board.D13)
        self.lcd_d7 = digitalio.DigitalInOut(board.D26)

        self.lcd_columns = 16
        self.lcd_rows = 2

        self.lcd = characterlcd.Character_LCD_Mono(
            self.lcd_rs,
            self.lcd_en,
            self.lcd_d4,
            self.lcd_d5,
            self.lcd_d6,
            self.lcd_d7,
            self.lcd_columns,
            self.lcd_rows,
        )
        self.lcd.clear()

    def cleanupDisplay(self):
        self.lcd.clear()
        self.lcd_rs.deinit()
        self.lcd_en.deinit()
        self.lcd_d4.deinit()
        self.lcd_d5.deinit()
        self.lcd_d6.deinit()
        self.lcd_d7.deinit()

    def updateScreen(self, message: str):
        self.lcd.clear()
        self.lcd.message = message


screen = ManagedDisplay()


class TemperatureMachine(StateMachine):
    """State machine for the thermostat."""

    off = State(initial=True)
    heat = State()
    cool = State()

    # Default temperature setPoint is 72°F
    setPoint = 72

    cycle = (off.to(heat) | heat.to(cool) | cool.to(off))

    # Used to keep callbacks and the display thread from stepping on each other
    _lock = Lock()

    # Control flag for display thread shutdown
    endDisplay = False

    def on_enter_heat(self):
        with self._lock:
            blueLight.off()
            self.updateLights()
        if DEBUG:
            print("* Changing state to heat")

    def on_exit_heat(self):
        with self._lock:
            # stop any red pulsing and turn it off before leaving
            redLight.off()

    def on_enter_cool(self):
        with self._lock:
            redLight.off()
            self.updateLights()
        if DEBUG:
            print("* Changing state to cool")

    def on_exit_cool(self):
        with self._lock:
            # stop any blue pulsing and turn it off before leaving
            blueLight.off()

    def on_enter_off(self):
        with self._lock:
            redLight.off()
            blueLight.off()
        if DEBUG:
            print("* Changing state to off")

    def processTempStateButton(self):
        if DEBUG:
            print("Cycling Temperature State")
        with self._lock:
            self.cycle()
            self.updateLights()

    def processTempIncButton(self):
        if DEBUG:
            print("Increasing Set Point")
        with self._lock:
            self.setPoint += 1
            self.updateLights()

    def processTempDecButton(self):
        if DEBUG:
            print("Decreasing Set Point")
        with self._lock:
            self.setPoint -= 1
            self.updateLights()

    def getFahrenheit(self) -> float:
        t_c = thSensor.temperature
        return ((9 / 5) * t_c) + 32

        def updateLights(self):
            """Update LEDs based on current state and temperature vs setPoint."""
            temp_f = floor(self.getFahrenheit())

            # Default: both off, then selectively enable
            redLight.off()
            blueLight.off()

            state_id = self.current_state.id  # "off", "heat", or "cool"

            if DEBUG:
                print(f"State: {state_id}")
                print(f"SetPoint: {self.setPoint}")
                print(f"Temp: {temp_f}")

            # OFF: nothing lit
            if state_id == "off":
                return

            # HEAT: red indicates
            if state_id == "heat":
                blueLight.off()
                if temp_f < self.setPoint:
                    redLight.pulse()   # fade in/out
                else:
                    redLight.on()      # solid when currentTemp >= setPoint
                return

            # COOL: blue indicates
            if state_id == "cool":
                redLight.off()
                if temp_f > self.setPoint:
                    blueLight.pulse()  # fade in/out
                else:
                    blueLight.on()     # solid when currentTemp <= setPoint
                return

def setupSerialOutput(self) -> str:
        """Create the UART output string: state,currentTemp,setPoint"""
        temp_f = floor(self.getFahrenheit())
        output = f"{self.current_state.id},{temp_f},{self.setPoint}\n"
        return output

    def run(self):
        myThread = Thread(target=self.manageMyDisplay, daemon=True)
        myThread.start()

    def manageMyDisplay(self):
        counter = 1       # seconds counter for UART (30 seconds)
        altCounter = 1    # toggles LCD line 2 content

        while not self.endDisplay:
            if DEBUG:
                print("Processing Display Info...")

            current_time = datetime.now()

            # Line 1: date/time (fits 16 chars)
            lcd_line_1 = current_time.strftime("%m/%d %H:%M:%S\n")

            # Line 2 alternates:
            # - first 5 seconds show current temperature
            # - next 5 seconds show state + setPoint
            with self._lock:
                temp_f = floor(self.getFahrenheit())
                state_text = self.current_state.id.upper()

                if altCounter < 6:
                    lcd_line_2 = f"Temp: {temp_f:>3}F\n"
                    altCounter += 1
                else:
                    # Example: "HEAT SP: 72F"
                    lcd_line_2 = f"{state_text:<4} SP:{self.setPoint:>3}F\n"
                    altCounter += 1

                    if altCounter >= 11:
                        # keep LEDs in sync even if temperature changes
                        self.updateLights()
                        altCounter = 1

            screen.updateScreen(lcd_line_1 + lcd_line_2)

            # UART output every 30 seconds
            if DEBUG:
                print(f"Counter: {counter}")

            if (counter % 30) == 0:
                try:
                    ser.write(self.setupSerialOutput().encode("utf-8"))
                    ser.flush()
                except Exception as ex:
                    if DEBUG:
                        print(f"UART send failed: {ex}")
                counter = 1
            else:
                counter += 1

            sleep(1)

        screen.cleanupDisplay()


# Setup state machine and start display thread
tsm = TemperatureMachine()
tsm.run()

# Buttons (GPIO interrupts via callbacks)
# NOTE: gpiozero uses BCM numbering by default.
MODE_PIN = 25  # user wiring: button 1 to GPIO25 and GND
SET_PIN = 12   # user wiring: button 2 to GPIO12 and GND

# Use internal pull-ups because the buttons are wired to GND.
modeButton = Button(MODE_PIN, pull_up=True, bounce_time=0.05)
setButton = Button(SET_PIN, pull_up=True, bounce_time=0.05)

# Long-press threshold (seconds) for SET button.
SET_HOLD_SECONDS = 0.8
_set_press_started_at = 0.0


def _on_set_pressed():
    global _set_press_started_at
    _set_press_started_at = monotonic()


def _on_set_released():
    duration = monotonic() - _set_press_started_at
    # Short press = UP, long press = DOWN
    if duration >= SET_HOLD_SECONDS:
        tsm.processTempDecButton()
    else:
        tsm.processTempIncButton()


modeButton.when_pressed = tsm.processTempStateButton
setButton.when_pressed = _on_set_pressed
setButton.when_released = _on_set_released

# Main loop: keep program alive until CTRL-C
repeat = True
while repeat:
    try:
        sleep(30)
    except KeyboardInterrupt:
        print("Cleaning up. Exiting...")
        repeat = False
        tsm.endDisplay = True
        sleep(1)
