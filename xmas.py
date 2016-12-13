######################
##### LED ALARM CLOCK - Using Adafruit's LED strips and Dexter Industry's GrovePi
##### TODO: Solve this weird global issue. Switch to instance variables?
######################

from neopixel import *
from grovepi import *
from grove_rgb_lcd import *
import grovepi
import time
import datetime
import RPi.GPIO as GPIO

# relay attempt 1
GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.OUT)
GPIO.output(26, GPIO.LOW)
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
strip2 = Adafruit_NeoPixel(LED_COUNT, LED_PIN2, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)

######################
##### ALARM TIMES
######################

TIME_TO_PREHEAT = 15
TIME_TILL_ANNOY = 10
TIME_TILL_SHUTOFF = 20
# alarm toggle
alarm_set = False
# load a default value for time
alarm_time = datetime.datetime.now()
# this alarm only needs hours and minutes
alarm_time = alarm_time.replace(year=2017, month=1, day=1, second=0, microsecond=0)
screen_on = False
alarm_running = False
# shhh is used to prevent the alarm from coming right back on when silenced
shhh = False

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
    global strip1, alarm_running, strip2
    # Intialize the neopixel library (must be called once before other functions).
    strip1.begin()
    strip2.begin()
    colorWipe(strip1, Color(255, 255, 255))
    alarm_running = True
    # TODO: trigger relay for heater


def shutoff():
    global strip1, strip2, alarm_running, shhh
    alarm_running = False
    # prevent alarm from coming right back on
    shhh = True
    print('Shutting off')
    killScreen()
    # turn off the heater
    GPIO.output(26, GPIO.LOW)
    # turn off the lights
    if strip1:
        colorWipe(strip1, Color(0, 0, 0), wait_ms=10)
    if strip2:
        colorWipe(strip2, Color(0, 0, 0), wait_ms=10)

def annoy():
    print('Snooze is over')
    # TODO: Buzzer
    # TODO: Rainbow

# send message to GrovePi LCD screen
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

# display options
def showMenu():
    # load our variables; because defining scope is weird
    global alarm_set, screen_on, alarm_time
    # timer to auto shut off the screen after 5 min
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
                # button1 will exit
                if grovepi.digitalRead(button1) == 1:
                    # let's double-check      
                    time.sleep(.1)
                    # exit the menu
                    if grovepi.digitalRead(button1) == 1:
                        return
                # button2 toggles the alarm
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
        # TODO: Prevent alarm from restarting after being disabled

        # trigger floor heater in advance of alarm
        if alarm_set and current_time == (alarm_time - datetime.timedelta(minutes = TIME_TO_PREHEAT)):
            # try to trigger the heater
            GPIO.output(26, GPIO.HIGH)

        # trigger alarm
        if alarm_set and current_time == alarm_time and not alarm_running and not shhh:
            wakeup()
        # annoy you until awake
        if alarm_set and alarm_running and current_time == (alarm_time + datetime.timedelta(minutes = TIME_TILL_ANNOY)):
            annoy()
        # auto shut-off
        if alarm_set and alarm_running and current_time == (alarm_time + datetime.timedelta(minutes = TIME_TILL_SHUTOFF)):
            shutoff()
        # button2 disables the alarm
        if grovepi.digitalRead(button2) == 1:
            shutoff()
        ## show screen options
        if grovepi.digitalRead(button1) == 1:
            showMenu()

        if current_time > alarm_time:
            shhh = False

        killScreen()
        message = ("%s : %s || On: " + str(alarm_set)) % (alarm_time.strftime("%H"), alarm_time.strftime("%M"))
        print("button1: %d || button2: %d \nAlarm: %s\n") % (grovepi.digitalRead(button1), grovepi.digitalRead(button2), message)
        # the longer this is, the longer you have to hold the button
        time.sleep(.5)
