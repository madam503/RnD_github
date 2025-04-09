import os
import math
import time
import argparse
import threading
import queue
from message_queue import message_queue
from collections import deque
import concurrent.futures

import numpy as np
from PIL import Image
import busio
import RPi.GPIO as GPIO

# Initialize GPIO
GPIO.setmode(GPIO.BCM)

# TensorFlow-related modules and custom operation definition
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import DepthwiseConv2D as tfDepthwiseConv2D

def custom_depthwise_conv2d(*args, **kwargs):
    kwargs.pop("groups", None)
    return tfDepthwiseConv2D(*args, **kwargs)

# Set file paths for model and labels (modify paths as needed)
MODEL_PATH = "keras_model.h5"
LABELS_PATH = "labels.txt"

# Load the model and labels
model = load_model(MODEL_PATH, custom_objects={"DepthwiseConv2D": custom_depthwise_conv2d}, compile=False)
with open(LABELS_PATH, "r", encoding="utf-8") as f:
    class_names = f.readlines()

np.set_printoptions(suppress=True, precision=4)

# Constants
TRIGGER_TEMP = 35            # Temperature threshold to trigger classification
COLORDEPTH = 1000            # Number of colors in the colormap
INTERPOLATE = 10             # Image interpolation scale factor
MINTEMP = 20.0               # Minimum temperature (°C)
MAXTEMP = 50.0               # Maximum temperature (°C)

# Define the heatmap (tuple: (ratio, (R, G, B)))
heatmap = (
    (0.0, (0, 0, 0)),
    (0.20, (0, 0, 0.5)),
    (0.40, (0, 0.5, 0)),
    (0.60, (0.5, 0, 0)),
    (0.80, (0.75, 0.75, 0)),
    (0.90, (1.0, 0.75, 0)),
    (1.00, (1.0, 1.0, 1.0)),
)

class ThermalDetector:
    def __init__(self, disable_interpolation=False):
        """
        Initialize the ThermalDetector.

        Parameters:
            disable_interpolation (bool): Whether to disable image interpolation.
        """
        self.disable_interpolation = disable_interpolation
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        # Create the colormap
        self.colormap = [None] * COLORDEPTH
        for i in range(COLORDEPTH):
            self.colormap[i] = self.gradient(i, COLORDEPTH, heatmap)

        # Initialize frame data (MLX90640 has 32 * 24 = 768 pixels)
        self.frame = [0] * 768

        # Log for emotion-related classification (e.g., "laydown")
        self.laydown_log = deque()

        # Flags for detection and classification status
        self.classification_active = False

        # Initialize I2C and MLX90640 sensor
        # (Pins 3 and 2 refer to Raspberry Pi I2C pins; modify if needed)
        self.i2c = busio.I2C(3, 2, frequency=400000)
        import adafruit_mlx90640
        self.mlx = adafruit_mlx90640.MLX90640(self.i2c)
        self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
        time.sleep(2)  # Allow sensor to stabilize

    def constrain(self, val, min_val, max_val):
        """Constrain a value between min_val and max_val."""
        return min(max_val, max(min_val, val))

    def gaussian(self, x, a, b, c, d=0):
        """Gaussian function."""
        return a * math.exp(-((x - b) ** 2) / (2 * c**2)) + d

    def gradient(self, x, width, cmap, spread=1):
        """Calculate the gradient color from the colormap."""
        width = float(width)
        r = sum(self.gaussian(x, p[1][0], p[0] * width, width / (spread * len(cmap))) for p in cmap)
        g = sum(self.gaussian(x, p[1][1], p[0] * width, width / (spread * len(cmap))) for p in cmap)
        b = sum(self.gaussian(x, p[1][2], p[0] * width, width / (spread * len(cmap))) for p in cmap)
        r = int(self.constrain(r * 255, 0, 255))
        g = int(self.constrain(g * 255, 0, 255))
        b = int(self.constrain(b * 255, 0, 255))
        return (r, g, b)

    def thermal_camera_basic(self):
        """
        Retrieve a frame from the MLX90640 sensor and generate a thermal image.
        The image is resized based on the interpolation setting.
        """
        try:
            self.mlx.getFrame(self.frame)
        except (ValueError, RuntimeError) as e:
            print("MLX90640 read error:", e)
            time.sleep(0.05)
            return None

        pixels = [None] * 768
        for i, pixval in enumerate(self.frame):
            # Calculate the color map index for the pixel temperature
            color_idx = int(max(0, min(COLORDEPTH - 1, (pixval - MINTEMP) * (COLORDEPTH - 1) / (MAXTEMP - MINTEMP))))
            pixels[i] = self.colormap[color_idx]

        # Create an image with resolution (32, 24) and assign pixel data
        img = Image.new("RGB", (32, 24))
        img.putdata(pixels)

        # If interpolation is enabled, enlarge the image
        if not self.disable_interpolation:
            img = img.resize((32 * INTERPOLATE, 24 * INTERPOLATE), Image.BICUBIC)

        return img

    def get_classify(self, image):
        try:
            classification_img = image.resize((224, 224), Image.Resampling.LANCZOS)
            img_array = np.asarray(classification_img, dtype=np.float32)
            normalized_img_array = (img_array / 127.5) - 1.0
            data = np.expand_dims(normalized_img_array, axis=0)
            prediction = model.predict(data)
            pred_index = np.argmax(prediction)
            class_name = class_names[pred_index].strip()

            self.laydown_log.append(class_name)
            if len(self.laydown_log) == 11:
                laydown_count = self.laydown_log.count("laydown")
                try:
                    import emotion
                    if laydown_count >= 9:
                        message_queue.put("gloomy")
                        print("[Detection.py] gloomy put in queue", message_queue.qsize())
                    else:
                        message_queue.put("happy")
                        print("[Detection.py] happy put in queue", message_queue.qsize())
                except Exception as e:
                    print("Failed to send signal to emotion module:", e)
                self.laydown_log.clear()

            return class_name
        except Exception as e:
            print("Classification error:", e)
            return None

    def classify_frame(self, image):
        """
        Obtain and print the classification result for the image.
        This method is intended to be run in a separate thread.
        """
        result = self.get_classify(image)
        print("Classification result:", result)
        return result

    def check_threshold(self):
        try:
            self.mlx.getFrame(self.frame)
        except (ValueError, RuntimeError) as e:
            print("MLX90640 read error in check_threshold:", e)
            return False
        current_max_temp = max(self.frame)
        return current_max_temp > TRIGGER_TEMP
        
    def classify_once(self):
        img = self.thermal_camera_basic()
        if img is None:
            print("Failed to acquire image for classification")
            return None
        result = self.get_classify(img)
        return result

    def run(self):
        """
        Main loop to continuously capture and classify thermal images.
        When the current temperature exceeds the threshold, classification is triggered,
        and images are classified periodically for 10 seconds.
        """
        running = True
        last_classification_time = time.monotonic() - 1
        classification_active_until = None
        detection_triggered = False

        try:
            while running:
                start_time = time.monotonic()

                img = self.thermal_camera_basic()
                current_max_temp = max(self.frame)
                current_time = time.monotonic()

                if img is None:
                    print("Failed to acquire image, exiting loop")
                    break

                if classification_active_until is None:
                    if current_max_temp > TRIGGER_TEMP and not detection_triggered:
                        classification_active_until = current_time + 10
                        detection_triggered = True
                        self.classification_active = True
                        
                        #threading.Thread(target=self.classify_frame, args=(img,)).start()
                        self.executor.submit(self.classify_frame, img)
                        last_classification_time = current_time

                    if current_max_temp <= TRIGGER_TEMP:
                        detection_triggered = False

                else:
                    if (current_time - last_classification_time) >= 1.0:
                        threading.Thread(target=self.classify_frame, args=(img,)).start()
                        last_classification_time = current_time

                    if current_time >= classification_active_until:
                        classification_active_until = None
                        detection_triggered = False
                        self.classification_active = False

                #end_time = time.monotonic()
                #loop_time = end_time - start_time
                #fps = 1.0 / loop_time if loop_time > 0 else 0
                # Loop delay (adjust as needed)
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("Exiting due to user request.")
        finally:
            self.executor.shutdown(wait=True)
            

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--disable-interpolation", action="store_true",
                        help="Disable image interpolation")
    return parser.parse_args()

def main():
    args = parse_arguments()
    detector = ThermalDetector(disable_interpolation=args.disable_interpolation)
    print("[Detection.py] DETECTOR START")
    detector.run()

if __name__ == '__main__':
    main()
