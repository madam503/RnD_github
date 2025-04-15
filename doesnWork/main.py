import time
import threading
import sonar_lib
import action_lib
import detection
import emotion
import gpio_manager
from robot_lib import motor_stop

THRESHOLD_DISTANCE = 15 
stop_event = threading.Event()

def petbot_loop():
    try:
        while not stop_event.is_set():
            if not message_queue.empty():
                classification_result = message_queue.get()
                if classification_result == "gloomy":
                    motor_stop()
                    time.sleep(2)
                    continue
                elif classification_result == "happy":
                    continue
             
            distance = sonar_lib.sonarDistance()
            if distance is None or distance < THRESHOLD_DISTANCE:
                action_lib.action_with_obstacle()
            else:
                action_lib.action_no_obstacle()
                
            time.sleep(0.1)
                    
    except Exception as e:
        print("An error occurred in petbot_loop:", e)

def main():
    gpio_manager.initialize()
    stop_event.clear()
    detector = detection.ThermalDetector(disable_interpolation=False)
    
    motor_thread = threading.Thread(target=petbot_loop, daemon=True)
    detection_thread = threading.Thread(target=detector.run, daemon=True)
    emotion_thread = threading.Thread(target=emotion.main, daemon=True)
    
    motor_thread.start()
    detection_thread.start()
    emotion_thread.start()
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stop requested by user.")
        stop_event.set()
        motor_thread.join()
        detection_thread.join()
        emotion_thread.join()
    finally:
        motor_stop()
        gpio_manager.cleanup()
    
if __name__ == '__main__':
    main()
