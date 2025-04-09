import time
import threading
import sonar_lib
import action_lib
import detection
import emotion
import RPi.GPIO as GPIO
from robot_lib import motor_stop

GPIO.setmode(GPIO.BCM)

THRESHOLD_DISTANCE = 15 
stop_event = threading.Event()

def petbot_loop():
    try:
        while not stop_event.is_set():
            distance = sonar_lib.sonarDistance()
            if distance is None or distance < THRESHOLD_DISTANCE:
                action_lib.action_with_obstacle()
            else:
                action_lib.action_no_obstacle()
            time.sleep(0.1)
    except Exception as e:
        print("An error occurred in petbot_loop:", e)

def main():
    stop_event.clear()
    
    detector = detection.ThermalDetector(disable_interpolation=False)
    
    motor_thread = threading.Thread(target=petbot_loop)
    detection_thread = threading.Thread(target=detector.run)
    emotion_thread = threading.Thread(target=emotion.main)
    
    motor_thread.start()
    detection_thread.start()
    emotion_thread.start()
    
    try:
        while True:
            if detector.check_threshold():
                print("High temperature detected, stopping motor thread.")
                stop_event.set()     
                motor_thread.join()  
                print("Motor thread has been terminated")
                
                classification_result = detector.classify_once()
                print("classification result", classification_result)
                
                print("Classification finished. restarting motor thread")
                stop_event.clear()  
                motor_thread = threading.Thread(target=petbot_loop)
                motor_thread.start()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stop requested by user.")
        stop_event.set()
        motor_thread.join()
        detection_thread.join()
        emotion_thread.join()
    finally:
        motor_stop()
        GPIO.cleanup()
    
if __name__ == '__main__':
    main()
