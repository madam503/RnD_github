import time
import Jetson.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

motor1_pin = [35, 36]
motor2_pin = [37, 38]
m1f, m1b = motor1_pin[0], motor1_pin[1]
m2f, m2b = motor2_pin[0], motor2_pin[1]

GPIO.setup(m1f, GPIO.OUT, initial=0)
GPIO.setup(m1b, GPIO.OUT, initial=0)
GPIO.setup(m2f, GPIO.OUT, initial=0)
GPIO.setup(m2b, GPIO.OUT, initial=0)

def motor_forward():
    print("forward")
    GPIO.output(m1f, 1)
    GPIO.output(m1b, 0)    
    GPIO.output(m2f, 1)
    GPIO.output(m2b, 0)

def motor_backward():
    print("backward")
    GPIO.output(m1f, 0)
    GPIO.output(m1b, 1)    
    GPIO.output(m2f, 0)
    GPIO.output(m2b, 1)

def turn_right():
    print("turn right")
    GPIO.output(m1f, 1)
    GPIO.output(m1b, 0)    
    GPIO.output(m2f, 0)
    GPIO.output(m2b, 1)
    time.sleep(0.5)
    motor_stop()

def turn_left():
    print("turn left")
    GPIO.output(m1f, 0)
    GPIO.output(m1b, 1)    
    GPIO.output(m2f, 1)
    GPIO.output(m2b, 0)
    time.sleep(0.5)
    motor_stop()

def motor_stop():
    print("stop")
    GPIO.output(m1f, 0)
    GPIO.output(m1b, 0)    
    GPIO.output(m2f, 0)
    GPIO.output(m2b, 0)

def main():
    try:
        while True:
            turn_right()
            turn_right()
            turn_right()
            turn_left()
            turn_right()
            turn_right()

    except KeyboardInterrupt:
        print("stop by man")
        motor_stop()

    finally:
        GPIO.cleanup()
        print("GPIO cleanup Complete")

if __name__=='__main__':
    main()
