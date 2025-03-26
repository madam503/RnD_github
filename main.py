import time
import random
import sonar_lib
import action_lib
import Jetson.GPIO as GPIO

THRESHOLD = 20

def main():
    try:
        while True:
            distance = sonar_lib.sonarDistance()
            if distance is None or distance < THRESHOLD:
                action_lib.action_with_obstacle()
            else:
                action_lib.action_no_obstacle()
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("stop by man")

    finally:
        from robot_lib import motor_stop
        motor_stop()
        GPIO.cleanup()
        print("GPIO Cleanup")

if __name__ == '__main__':
    main()















