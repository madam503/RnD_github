import RPi.GPIO as GPIO

def initialize():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
def cleanup():
    GPIO.cleanup()
