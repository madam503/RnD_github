import math
import time
import numpy as np
from PIL import Image
import board
import busio
import adafruit_mlx90640
import pygame

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

INTERPOLATE = 10
MINTEMP = 20.0
MAXTEMP = 50.0
COLORDEPTH = 1000

def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def gaussian(x, a, b, c, d=0):
    return a * math.exp(-((x - b)**2) / (2 * c**2)) + d

def gradient(x, width, cmap, spread=1):
    width = float(width)
    r = sum(gaussian(x, p[1][0], p[0]*width, width/(spread*len(cmap))) for p in cmap)
    g = sum(gaussian(x, p[1][1], p[0]*width, width/(spread*len(cmap))) for p in cmap)
    b = sum(gaussian(x, p[1][2], p[0]*width, width/(spread*len(cmap))) for p in cmap)
    r = int(constrain(r, 255, 0, 255))
    g = int(constrain(g, 255, 0, 255))
    b = int(constrain(b, 255, 0, 255))
    return r, g, b

heatmap = (
    (0.0, (0, 0, 0)),
    (0.20, (0, 0, 0.5)),
    (0.40, (0, 0.5, 0)),
    (0.60, (0.5, 0, 0)),
    (0.80, (0.75, 0.75, 0)),
    (0.90, (1.0, 0.75, 0)),
    (1.00, (1.0, 1.0, 1.0)))

colormap = [gradient(i, COLORDEPTH, heatmap) for i in range(COLORDEPTH)]

i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000)
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
time.sleep(2)
frame = [0] * 768

def get_detection_data(disable_interpolation=False):
    try:
        mlx.getFrame(frame)
    except Exception as e:
        print("MLX90640 read error:", e)
        return None
    
    pixels = []
    for pixval in frame:
        idx = map_value(pixval, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1)
        idx = int(constrain(idx, 0, COLORDEPTH - 1))
        pixels.append(colormap[idx])
        
    img = Image.new("RGB", (32, 24))
    img.putdata(pixels)
    if not disable_interpolation:
        img = img.resize((32 * INTERPOLATE, 24 * INTERPOLATE), Image.BICUBIC)
        
    current_max_temp = max(frame)
    classification_result = None
    
    if current_max_temp >= 36.5:
        try:
            classification_img = img.resize((224, 224), Inage.Resampling.LANCZOS)
            img_array = np.asarray(classification_img, dtype=np.float32)
            normalized_img_array = (img_array / 127.5) - 1.0
            data = np.expand_dims(normalized_img_array, axis=0)
            prediction = model.predict(data)
            pred_index = np.argmax(prediction)
            classification_result = class_names[pred_index].strip().lower()
        except Exception as e:
            print("Classification error:", e)
            
    return {
        "img": img,
        "current_max_temp": current_max_temp,
        "classification_result": classification_result
        }






























