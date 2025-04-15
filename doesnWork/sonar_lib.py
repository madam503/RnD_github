import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

TRIG = 14
ECHO = 15

GPIO.setup(TRIG, GPIO.OUT) 
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, False)

time.sleep(2)

def sonarDistance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start_time = time.perf_counter()
    timeout = start_time + 0.02
    while GPIO.input(ECHO) == 0 and time.perf_counter() < timeout:
        start_time = time.perf_counter()
    if time.perf_counter() >= timeout:
        return None
    
    end_time = time.perf_counter()
    timeout = end_time + 0.02
    while GPIO.input(ECHO) == 1 and time.perf_counter() < timeout:
        end_time = time.perf_counter()
    if time.perf_counter() >= timeout:
        return None

    pulse_duration = end_time - start_time
    distance = pulse_duration * 17150
    
    if distance < 1:
        return None

    return round(distance, 2)

def main():
    try:
        while True:
            distance = sonarDistance()
            if distance is None:
                print("Too close!")
            else:
                print("Distance: {} cm".format(distance))
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nSonar sensor stopped by User")
    finally:
        GPIO.cleanup()

if __name__=='__main__':
    main()
