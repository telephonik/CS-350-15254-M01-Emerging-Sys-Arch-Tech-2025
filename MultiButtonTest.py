#
# MultiButtonTest.py
#
# Quick hardware test for multiple buttons and PWMLED controls (gpiozero).
#
# Hardware constraint: only TWO buttons available.
# - MODE button (GPIO25): both LEDs solid
# - SET button  (GPIO12): short press -> red fades, long press -> blue fades
#
from time import monotonic
from gpiozero import Button, PWMLED
from signal import pause

DEBUG = True

red = PWMLED(18)
blue = PWMLED(23)

def bothOn():
    if DEBUG:
        print("* Both LEDs on")
    red.off()
    blue.off()
    red.on()
    blue.on()

def redFade():
    if DEBUG:
        print("* Fading Red")
    blue.off()
    red.pulse()

def blueFade():
    if DEBUG:
        print("* Fading Blue")
    red.off()
    blue.pulse()

MODE_PIN = 25  # button 1 wired to GPIO25 and GND
SET_PIN = 12   # button 2 wired to GPIO12 and GND

modeButton = Button(MODE_PIN, pull_up=True, bounce_time=0.05)
setButton = Button(SET_PIN, pull_up=True, bounce_time=0.05)

# MODE button turns both LEDs solid (quick sanity check).
modeButton.when_pressed = bothOn

# SET button: short press -> red fades; long press -> blue fades.
SET_HOLD_SECONDS = 0.8
_set_press_started_at = 0.0


def _on_set_pressed():
    global _set_press_started_at
    _set_press_started_at = monotonic()


def _on_set_released():
    duration = monotonic() - _set_press_started_at
    if duration >= SET_HOLD_SECONDS:
        blueFade()
    else:
        redFade()


setButton.when_pressed = _on_set_pressed
setButton.when_released = _on_set_released

# Keep the script running so callbacks continue to work
pause()
