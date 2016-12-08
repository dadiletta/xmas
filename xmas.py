######################
##### LED ALARM CLOCK - Using Adafruit's LED strips and Dexter Industry's GrovePi
######################

from neopixel import *
from grovepi import *
from grove_rgb_lcd import *
import grovepi
import time
import datetime

######################
##### LED INFO
######################

LED_COUNT = 60  # Number of LED pixels.
LED_PIN1 = 18  # GPIO pin connected to the pixels (must support PWM!).
LED_PIN2 = 23
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 5  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)

######################
##### ALARM TIMES
######################

TIME_TILL_ANNOY = 10
TIME_TILL_SHUTOFF = 20
# alarm toggle
alarmOn = False
# load a default value for time
alarm_time = datetime.datetime.now()
# this alarm only needs hours and minutes
alarm_time = alarm_time.replace(year=2017, month=1, day=1, second=0, microsecond=0)
screen_on = False

######################
##### GROVEPI SETUP
######################

buzzer = 6
grovepi.pinMode(buzzer,"OUTPUT")

# Connect the Grove Button to digital port D8
button1 = 8
button2 = 7
grovepi.pinMode(button1,"INPUT")
grovepi.pinMode(button2,"INPUT")

######################
##### LED METHODS
######################

def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)

def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, color)
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)

def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)

def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, wheel((i + j) % 255))
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)


######################
##### ALARM METHODS
######################

def wakeup():
    print('Waking up')

def shutoff():
    print('Shutting off')
    killScreen()

def annoy():
    print('Snooze is over')

def showStatus(highlight):
    global screen_on
    print('Displaying screen with %s highlighted') % highlight
    screen_on = True
    if highlight == "time":
        setRGB(150, 75, 0)
        message = ("-> %s : %s <- \nOn: " + str(alarmOn)) % (alarm_time.strftime("%H"), alarm_time.strftime("%M"))
        setText(message)
    else:
        setRGB(0, 150, 75)
        message = ("%s : %s  \n-> On: " + str(alarmOn) + " <-") % (alarm_time.strftime("%H"), alarm_time.strftime("%M"))
        setText(message)


def killScreen():
    global screen_on
    if screen_on:
        print('Killing the display')
        textCommand(0x01) # clear display
        time.sleep(.05)
        setRGB(0,0,0)
        time.sleep(.05)
        screen_on = False

def showMenu():
    global alarmOn
    global screen_on
    global alarm_time
    menu_start = datetime.datetime.now()
    while datetime.datetime.now() < menu_start + datetime.timedelta(minutes=5):
        # this check is to avoid flashing the LCD screen repeatidly
        if not screen_on:
            showStatus("time")
        time.sleep(.1)

        ## change to edit the alarm on/off toggle
        if grovepi.digitalRead(button1) == 1:
            screen_on = False
            menu_start = datetime.datetime.now()
            while datetime.datetime.now() < menu_start + datetime.timedelta(minutes=5):
                if not screen_on:
                    showStatus("toggle")
                time.sleep(.5)
                if grovepi.digitalRead(button1) == 1:
                    # let's double-check      
                    time.sleep(.1)
                    if grovepi.digitalRead(button1) == 1:
                        return
                if grovepi.digitalRead(button2) == 1:
                    alarmOn = not alarmOn
                    screen_on = False
        # advance the minutes of the time
        if grovepi.digitalRead(button2) == 1:
            alarm_time = alarm_time + datetime.timedelta(minutes=1)
            screen_on = False


######################
##### LOGIC
######################

# Main program logic follows:
if __name__ == '__main__':


    # MAIN APP LOOP
    while True:
        global alarmOn
        global alarm_time
        current_time = datetime.datetime.now()
        current_time = current_time.replace(year=2017, month=1, day=1, second=0, microsecond=0)
        if alarmOn and current_time == alarm_time:
            wakeup()
        if alarmOn and current_time == (alarm_time + datetime.timedelta(minutes = TIME_TILL_ANNOY)):
            annoy()
        if alarmOn and current_time == (alarm_time + datetime.timedelta(minutes = TIME_TILL_SHUTOFF)):
            shutoff()
        if grovepi.digitalRead(button2) == 1:
            shutoff()
        ## show screen
        if grovepi.digitalRead(button1) == 1:
            showMenu()

        killScreen()
        message = ("%s : %s || On: " + str(alarmOn)) % (alarm_time.strftime("%H"), alarm_time.strftime("%M"))
        print("button1: %d || button2: %d \nAlarm: %s\n") % (grovepi.digitalRead(button1), grovepi.digitalRead(button2), message)
        time.sleep(.5)
        


'''
    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    print('Press Ctrl-C to quit.')
    while True:
        # Color wipe animations.
        colorWipe(strip, Color(255, 0, 0))  # Red wipe
        colorWipe(strip, Color(0, 255, 0))  # Blue wipe
        colorWipe(strip, Color(0, 0, 255))  # Green wipe
        # Theater chase animations.
        theaterChase(strip, Color(127, 127, 127))  # White theater chase
        theaterChase(strip, Color(127, 0, 0))  # Red theater chase
        theaterChase(strip, Color(0, 0, 127))  # Blue theater chase
        # Rainbow animations.
        rainbow(strip)
        rainbowCycle(strip)
        theaterChaseRainbow(strip)
'''
