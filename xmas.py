######################
##### LED ALARM CLOCK - Using Adafruit's LED strips and Dexter Industry's GrovePi
##### TODO: Fix SHHHH... done?
##### TODO: Implement the annoy method
##### TODO: Switch clock to 12-hour on alarm set
##### TODO: Verify controls are easier to toggle
##### TODO: Add a temp sensor
##### TODO: Help! Replace while-loop with event handlers?
##### TODO: Help! Improve LED controls so specific LEDs can be managed
##### TODO: Help! Rewire LED strip with longer cables, solder into prototype board
######################

from neopixel import *
from grovepi import *
from grove_rgb_lcd import *
import grovepi
import time
import datetime
import requests
import Private


MAKER_SECRET = Private.Private.MAKER_SECRET

# Canceled using relay
# import RPi.GPIO as GPIO
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(26, GPIO.OUT)
# GPIO.output(26, GPIO.LOW)

######################
##### LED INFO
######################

LED_COUNT = 60  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ = 875000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 3  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 254  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
strip1 = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)

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
grovepi.pinMode(buzzer, "OUTPUT")

# Connect the Grove Button to digital port D8
button1 = 8
button2 = 7
grovepi.pinMode(button1, "INPUT")
grovepi.pinMode(button2, "INPUT")

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
    global strip1, alarm_running
    # Initialize the neopixel library (must be called once before other functions).
    strip1.begin()
    colorWipe(strip1, Color(255, 255, 255))
    alarm_running = True
    # Post to IFTTT on the Maker channel
    payload = "{ 'value1' : 'wakeup', 'value2' : 'hello', 'value3' : 'hello'}"
    requests.post("https://maker.ifttt.com/trigger/wakeup/with/key/" + MAKER_SECRET, data=payload)


def shutoff():
    global strip1, alarm_running, shhh
    alarm_running = False
    shhh = True
    # prevent alarm from coming right back on
    print('Shutting off')
    killScreen()
    # turn off the lights
    if strip1:
        colorWipe(strip1, Color(0, 0, 0), wait_ms=10)
    payload = "{ 'value1' : 'wakeup', 'value2' : 'hello', 'value3' : 'hello'}"
    requests.post("https://maker.ifttt.com/trigger/shutoff/with/key/" + MAKER_SECRET, data=payload)



def annoy():
    print('Snooze is over')
    payload = "{ 'value1' : 'hello', 'value2' : 'hello', 'value3' : 'hello'}"
    requests.post("https://maker.ifttt.com/trigger/annoy/with/key/" + MAKER_SECRET, data=payload)


# send message to GrovePi LCD screen
def showStatus(highlight):
    global screen_on
    print('Displaying screen with %s highlighted') % highlight
    screen_on = True
    # change display to help indicate what is being selected
    if highlight == "hour":
        setRGB(150, 75, 0)
        msg = ("--> %s : %s \nOn: " + str(alarm_set)) % (alarm_time.strftime("%H"), alarm_time.strftime("%M"))
        setText(msg)
    elif highlight == "min":
        setRGB(0, 75, 150)
        msg = ("%s : %s <-- \nOn: " + str(alarm_set)) % (alarm_time.strftime("%H"), alarm_time.strftime("%M"))
        setText(msg)
    else:
        setRGB(0, 150, 75)
        msg = ("%s : %s  \n-> On: " + str(alarm_set) + " <-") % (alarm_time.strftime("%H"), alarm_time.strftime("%M"))
        setText(msg)


def killScreen():
    global screen_on
    if screen_on:
        print('Killing the display')

        # this code taken from Dexter Industries's GrovePi examples
        textCommand(0x01)  # clear display
        time.sleep(.05)
        setRGB(0,0,0)
        time.sleep(.05)

        # update global boolean to help track status
        screen_on = False


# menu logic, careful options
def menu():
    # load our variables; because defining scope is weird
    global alarm_set, shhh, screen_on, alarm_time, alarm_running
    # disable the hold on (re)starting the alarm
    shhh = False
    # timer to auto shut off the screen after 5 min
    menu_start = datetime.datetime.now()
    # INITIAL STATE: EDITING HOURS
    while datetime.datetime.now() < menu_start + datetime.timedelta(minutes=5):
        # this check is to avoid flashing the LCD screen repeatedly
        if not screen_on:
            showStatus("hour")
        time.sleep(.4)

        # BUTTON2: advance the hours of the time
        if grovepi.digitalRead(button2) == 1:
            alarm_time = alarm_time + datetime.timedelta(hours=1)
            screen_on = False

        # BUTTON1: change to edit minutes
        if grovepi.digitalRead(button1) == 1:
            screen_on = False
            menu_start = datetime.datetime.now()

            # STATE: EDITING MINUTES
            while datetime.datetime.now() < menu_start + datetime.timedelta(minutes=5):
                if not screen_on:
                    showStatus("min")
                time.sleep(.4)

                # BUTTON2: advance the minutes
                if grovepi.digitalRead(button2) == 1:
                    if alarm_time.strftime("%M") == "59":
                        alarm_time.replace(minute=0)
                    else:
                        alarm_time = alarm_time + datetime.timedelta(minutes=1)
                    screen_on = False

                # BUTTON1: change to edit alarm on/off toggle
                if grovepi.digitalRead(button1) == 1:
                    # screen_on False so it will refresh display
                    screen_on = False
                    menu_start = datetime.datetime.now()

                    # STATE: EDITING ALARM ON
                    while datetime.datetime.now() < menu_start + datetime.timedelta(minutes=5):
                        if not screen_on:
                            showStatus("toggle")
                        time.sleep(.4)

                        # BUTTON1: closes method (after double-check)
                        if grovepi.digitalRead(button1) == 1:
                            # let's double-check
                            time.sleep(.1)
                            # exit the menu
                            if grovepi.digitalRead(button1) == 1:
                                return

                        # BUTTON2: toggles the alarm
                        if grovepi.digitalRead(button2) == 1:
                            alarm_set = not alarm_set
                            # screen_on False so it refreshes display
                            screen_on = False
                            shhh = False
                            alarm_running = False



######################
##### LOGIC
######################

# Main program logic follows:
if __name__ == '__main__':

    count = 0

    # MAIN APP LOOP
    while True:

        current_time = datetime.datetime.now()
        current_time = current_time.replace(year=2017, month=1, day=1, second=0, microsecond=0)

        # display current time, (count used to avoid screen flashing)
        if count % 20 == 0:
            clock = ("Time: %s \nAlarm: %s On:" + str(alarm_set)) % \
                    (current_time.strftime("%I:%M %p"), alarm_time.strftime("%I:%M %p"))
            setText(clock)

        # trigger alarm
        if alarm_set and current_time == alarm_time and not alarm_running and not shhh:
            wakeup()
        # annoy you until awake
        if alarm_set and alarm_running and current_time == (alarm_time + datetime.timedelta(minutes=TIME_TILL_ANNOY)):
            annoy()
        # auto shut-off
        if alarm_set and alarm_running and current_time == (alarm_time + datetime.timedelta(minutes=TIME_TILL_SHUTOFF)):
            shutoff()
        # button2 disables the alarm
        if grovepi.digitalRead(button2) == 1 and alarm_running:
            shutoff()
        # show screen options
        if grovepi.digitalRead(button1) == 1:
            menu()

        if current_time > alarm_time:
            shhh = False

        killScreen()

        # console output for debugging
        message = ("%s : %s || On: " + str(alarm_set)) % (alarm_time.strftime("%H"), alarm_time.strftime("%M"))
        print("button1: %d || button2: %d \nAlarm: %s\n") % (grovepi.digitalRead(button1),
                                                             grovepi.digitalRead(button2), message)

        # the longer this is, the longer you have to hold the button
        time.sleep(.5)

        # counter used as sloppy way to prevent screen flashing in main loop
        count += 1
        if count > 1000:
            count = 0
