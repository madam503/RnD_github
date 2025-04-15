import threading
import random
import robot_lib

def random_normal_duration():
    return random.uniform(1, 3)

def slight_duration():
    return random.uniform(0.5, 1)

def action_no_obstacle():

    actions = [
        "forward","forward","forward",
        "backward",
        "idle",
        "turn_right_forward",
        "turn_right_backward",
        "turn_right_idle",
        "turn_left_forward",
        "turn_left_backward",
        "turn_left_idle"
    ]
    action = random.choice(actions)
    print(f"[NO OBSTALE] selected action: {action}")
    
    duration = random_normal_duration()

    if action == "forward":
        robot_lib.motor_forward()
        threading.Timer(duration, robot_lib.motor_stop).start()
    elif action == "backward":
        robot_lib.motor_backward()
        threading.Timer(duration, robot_lib.motor_stop).start()
    elif action == "idle":
        robot_lib.motor_stop()
    elif action == "turn_right_forward":
        robot_lib.turn_right()
        robot_lib.motor_forward()
        threading.Timer(duration, robot_lib.motor_stop).start()
    elif action == "turn_right_backward":
        robot_lib.turn_right()
        robot_lib.motor_backward()
        threading.Timer(duration, robot_lib.motor_stop).start()
    elif action == "turn_right_idle":
        robot_lib.turn_right()
        robot_lib.motor_stop()
    elif action == "turn_left_forward":
        robot_lib.turn_left()
        robot_lib.motor_forward()
        threading.Timer(duration, robot_lib.motor_stop).start()
    elif action == "turn_left_backward":
        robot_lib.turn_left()
        robot_lib.motor_backward()
        threading.Timer(duration, robot_lib.motor_stop).start()
    elif action == "turn_left_idle":
        robot_lib.turn_left()
        robot_lib.motor_stop()

def action_with_obstacle():
    actions = [
        "turn_right_forward",
        "turn_right_backward",
        "turn_left_forward",
        "turn_left_backward"
    ]

    action = random.choice(actions)
    print(f"[OBSTACLE] selected avoidance: {action}")
    
    duration = slight_duration()

    if action == "turn_right_forward":
        robot_lib.turn_right()
        robot_lib.motor_forward()
        threading.Timer(duration, robot_lib.motor_stop).start()
    elif action == "turn_right_backward":
        robot_lib.turn_right()
        robot_lib.motor_backward()
        threading.Timer(duration, robot_lib.motor_stop).start()
    elif action == "turn_left_forward":
        robot_lib.turn_left()
        robot_lib.motor_forward()
        threading.Timer(duration, robot_lib.motor_stop).start()
    elif action == "turn_left_backward":
        robot_lib.turn_left()
        robot_lib.motor_backward()
        threading.Timer(duration, robot_lib.motor_stop).start()

if __name__=="__main__":
    action_no_obstacle()
    action_with_obstacle()
