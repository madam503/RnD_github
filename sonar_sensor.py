import time
import Jetson.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
TRIG = 13
ECHO = 11

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

time.sleep(2)

def measure_distance():
    
    GPIO.output(TRIG, False)
    time.sleep(0.05)
    
    GPIO.output(TRIG, True)
    time.sleep(0.05)
    GPIO.output(TRIG, False)
    
    start_timeout = time.time() + 0.1
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if time.time() > start_timeout:
            return None
    
    pulse_end = pulse_start
    
    end_timeout = time.time() + 0.1
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if time.time() > end_timeout:
            return None

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    if distance >= 400:
        return 400
    else:
        return round(distance, 2)

last_distance = None

try:
    while True:
        distance = measure_distance()
        if distance is not None:
            last_distance = distance
            print("Distance: {} cm".format(distance))
        else:
            print("Measurement Error!!")
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nCtrl+C!!")
    if last_distance is not None:
        print("last distance : {} cm".format(last_distance))
    else:
        print("Dosn't measure a valid distance")

finally:
    GPIO.cleanup()
