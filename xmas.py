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
LED_FREQ_HZ = 875000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 3  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 254  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
strip1 = Adafruit_NeoPixel(LED_COUNT, LED_PIN1, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
#strip2 = Adafruit_NeoPixel(LED_COUNT, LED_PIN2, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)

######################
##### ALARM TIMES
######################

TIME_TILL_ANNOY = 10
TIME_TILL_SHUTOFF = 20
# alarm toggle
global alarm_set
alarm_set = False
# load a default value for time
global alarm_time
alarm_time = datetime.datetime.now()
# this alarm only needs hours and minutes
alarm_time = alarm_time.replace(year=2017, month=1, day=1, second=0, microsecond=0)
global screen_on
screen_on = False
global alarm_running
alarm_running = False

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

# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
        """Wipe color across display a pixel at a time."""
        for i in range(strip.numPixels()):
                if i % 5 == 0:
                        strip.setPixelColor(i, color)
                        strip.show()
                        time.sleep(wait_ms/1000.0)

######################
##### ALARM METHODS
######################

def wakeup():
    print('Waking up')
    global strip1
    global alarm_running
    #global strip2
    # Intialize the library (must be called once before other functions).
    strip1.begin()
    colorWipe(strip1, Color(255, 255, 255))
    alarm_running = True


def shutoff():
    global strip1
    #global strip2
    global alarm_running
    alarm_running = False
    print('Shutting off')
    killScreen()
    if strip1:
        colorWipe(strip1, Color(0, 0, 0), wait_ms=10)
        #strip1.__del__()
    #if strip2:
        #colorWipe(strip2, Color(0, 0, 0), wait_ms=10)
        #strip2.__del__()

def annoy():
    print('Snooze is over')

def showStatus(highlight):
    global screen_on
    print('Displaying screen with %s highlighted') % highlight
    screen_on = True
    if highlight == "time":
        setRGB(150, 75, 0)
        message = ("-> %s : %s <- \nOn: " + str(alarm_set)) % (alarm_time.strftime("%H"), alarm_time.strftime("%M"))
        setText(message)
    else:
        setRGB(0, 150, 75)
        message = ("%s : %s  \n-> On: " + str(alarm_set) + " <-") % (alarm_time.strftime("%H"), alarm_time.strftime("%M"))
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
    global alarm_set
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
                    alarm_set = not alarm_set
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
        current_time = datetime.datetime.now()
        current_time = current_time.replace(year=2017, month=1, day=1, second=0, microsecond=0)
        if alarm_set and current_time == alarm_time and not alarm_running:
            wakeup()
        if alarm_set and current_time == (alarm_time + datetime.timedelta(minutes = TIME_TILL_ANNOY)):
            annoy()
        if alarm_set and current_time == (alarm_time + datetime.timedelta(minutes = TIME_TILL_SHUTOFF)):
            shutoff()
        if grovepi.digitalRead(button2) == 1:
            shutoff()
        ## show screen
        if grovepi.digitalRead(button1) == 1:
            showMenu()

        killScreen()
        message = ("%s : %s || On: " + str(alarm_set)) % (alarm_time.strftime("%H"), alarm_time.strftime("%M"))
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
