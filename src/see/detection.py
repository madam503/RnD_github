import os
os.environ["SDL_VIDEODRIVER"] = "x11"
os.environ["DISPLAY"] = ":0.0"

import math
import time
import argparse
import numpy as np

from PIL import Image
import pygame
pygame.init()

from tensorflow.keras.models import load_model
from tensorflow.keras.layers import DepthwiseConv2D as tfDepthwiseConv2D

def custom_depthwise_conv2d(*args, **kwargs):
    kwargs.pop("groups", None)
    return tfDepthwiseConv2D(*args, **kwargs)

MODEL_PATH = "keras_model.h5"
LABELS_PATH = "labels.txt"

model = load_model(MODEL_PATH, custom_objects={"DepthwiseConv2D": custom_depthwise_conv2d}, compile=False)
class_names = open(LABELS_PATH, "r", encoding="utf-8").readlines()

np.set_printoptions(suppress=True, precision=4)

WINDOW_SCALING_FACTOR = 20
screen = pygame.display.set_mode([32 * WINDOW_SCALING_FACTOR, 24 * WINDOW_SCALING_FACTOR])
pygame.mouse.set_visible(False)
screen.fill((0, 0, 0))
pygame.display.update()

import board
import busio
import adafruit_mlx90640

parser = argparse.ArgumentParser()
parser.add_argument("--disable-interpolation", action="store_true",
                    help="disable interpolation between camera pixels")
args = parser.parse_args()

print(pygame.display.Info())

heatmap = (
    (0.0, (0, 0, 0)),
    (0.20, (0, 0, 0.5)),
    (0.40, (0, 0.5, 0)),
    (0.60, (0.5, 0, 0)),
    (0.80, (0.75, 0.75, 0)),
    (0.90, (1.0, 0.75, 0)),
    (1.00, (1.0, 1.0, 1.0)),
)

COLORDEPTH = 1000
colormap = [0] * COLORDEPTH

def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def gaussian(x, a, b, c, d=0):
    return a * math.exp(-((x - b) ** 2) / (2 * c**2)) + d

def gradient(x, width, cmap, spread=1):
    width = float(width)
    r = sum(gaussian(x, p[1][0], p[0] * width, width / (spread * len(cmap))) for p in cmap)
    g = sum(gaussian(x, p[1][1], p[0] * width, width / (spread * len(cmap))) for p in cmap)
    b = sum(gaussian(x, p[1][2], p[0] * width, width / (spread * len(cmap))) for p in cmap)
    r = int(constrain(r * 255, 0, 255))
    g = int(constrain(g * 255, 0, 255))
    b = int(constrain(b * 255, 0, 255))
    return r, g, b

for i in range(COLORDEPTH):
    colormap[i] = gradient(i, COLORDEPTH, heatmap)

def get_class_name(image):
    try:
        classification_img = image.resize((224, 224), Image.Resampling.LANCZOS)
        img_array = np.asarray(classification_img, dtype=np.float32)
        normalized_img_array = (img_array / 127.5) - 1.0
        data = np.expand_dims(normalized_img_array, axis=0)
        prediction = model.predict(data)
        pred_index = np.argmax(prediction)
        class_name = class_names[pred_index].strip()
        return class_name
    except Exception as e:
        print("Classification error:", e)
        return None

def get_max_temperature():
    current_max_temp = max(frame)
    return current_max_temp
    
i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000)
mlx = adafruit_mlx90640.MLX90640(i2c)

mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
time.sleep(2)

frame = [0] * 768

INTERPOLATE = 10
MINTEMP = 20.0
MAXTEMP = 50.0

current_max_temp = 0.0

running = True
while running:
    start_time = time.monotonic()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            pass

    try:
        mlx.getFrame(frame)
    except (ValueError, RuntimeError) as e:
        print("MLX90640 read error:", e)
        time.sleep(0.05)
        continue

    pixels = [0] * 768
    for i, pixval in enumerate(frame):
        coloridx = map_value(pixval, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1)
        coloridx = int(constrain(coloridx, 0, COLORDEPTH - 1))
        pixels[i] = colormap[coloridx]

    img = Image.new("RGB", (32, 24))
    img.putdata(pixels)

    if not args.disable_interpolation:
        img = img.resize((32 * INTERPOLATE, 24 * INTERPOLATE), Image.BICUBIC)

    img_surface = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
    scaled_surface = pygame.transform.scale(img_surface.convert(), screen.get_size())
    screen.blit(scaled_surface, (0, 0))
    pygame.display.update()
    pygame.event.pump()

    current_max_temp = get_max_temperature()

    font = pygame.font.SysFont("Arial", 20)
    temp_text = f"Max Temp: {current_max_temp:.1f} C"
    text_surface = font.render(temp_text, True, (255, 0, 0))
    screen.blit(text_surface, (10, 10))
    pygame.display.update()

    try:
        classification_img = img.resize((224, 224), Image.Resampling.LANCZOS)
        img_array = np.asarray(classification_img, dtype=np.float32)
        normalized_img_array = (img_array / 127.5) - 1.0
        data = np.expand_dims(normalized_img_array, axis=0)
        prediction = model.predict(data)
        pred_index = np.argmax(prediction)
        class_name = class_names[pred_index].strip()
        confidence_score = prediction[0][pred_index]
        print(f"[Inference] Class: {class_name}, Confidence: {confidence_score:.4f}")
    except Exception as e:
        print("Classification error:", e)

    end_time = time.monotonic()
    loop_time = end_time - start_time
    fps = 1.0 / loop_time if loop_time > 0 else 0
 
pygame.quit()
