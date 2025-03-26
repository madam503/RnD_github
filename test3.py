import os
os.environ["SDL_VIDEODRIVER"] = "x11"
os.environ["DISPLAY"] = ":0.0"

import math
import time
import argparse
from PIL import Image
import pygame
pygame.init()

# 저장 폴더가 없으면 생성합니다.
save_folder = "/home/hugo/Desktop/standup"
if not os.path.exists(save_folder):
    os.makedirs(save_folder)

# 작은 창 크기 설정 (32 x 24 픽셀을 WINDOW_SCALING_FACTOR로 확대)
WINDOW_SCALING_FACTOR = 20
screen = pygame.display.set_mode([32 * WINDOW_SCALING_FACTOR, 24 * WINDOW_SCALING_FACTOR])

import board
import busio
import adafruit_mlx90640

INTERPOLATE = 10  # 픽셀 보간 확대율

# 센서 온도 범위 설정 (MINTEMP: 최저, MAXTEMP: 최고)
MINTEMP = 20.0
MAXTEMP = 50.0

# 명령행 인수 파싱
parser = argparse.ArgumentParser()
parser.add_argument("--disable-interpolation", action="store_true", help="disable interpolation between camera pixels")
args = parser.parse_args()

print(pygame.display.Info())

# 히트맵 및 컬러맵 정의
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

pygame.mouse.set_visible(False)
screen.fill((0, 0, 0))
pygame.display.update()
sensorout = pygame.Surface((32, 24))

# I2C 초기화: 1MHz 주파수 사용
i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000)
mlx = adafruit_mlx90640.MLX90640(i2c)
print("MLX addr detected on I2C, Serial #", [hex(i) for i in mlx.serial_number])
# 안정성을 위해 리프레시 레이트를 2 Hz로 설정합니다.
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
time.sleep(2)  # 센서 안정화 시간

frame = [0] * 768
screenshot_count = 0  # 저장된 스크린샷 개수
saving_mode = False   # 'o' 키를 눌러 저장 모드를 토글

running = True
while running:
    start_time = time.monotonic()
    
    # 이벤트 처리: 'o' 키 입력으로 저장 모드를 켭니다.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # 'o' 키를 누르면 saving_mode를 활성화합니다.
            if event.key == pygame.K_o:
                saving_mode = True
                print("Saving mode activated: All frames will be saved.")

    try:
        mlx.getFrame(frame)
    except (ValueError, RuntimeError) as e:
        print("Error:", e)
        time.sleep(0.05)
        continue

    # 센서 프레임 데이터를 컬러 매핑
    pixels = [0] * 768
    for i, pixel in enumerate(frame):
        coloridx = map_value(pixel, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1)
        coloridx = int(constrain(coloridx, 0, COLORDEPTH - 1))
        pixels[i] = colormap[coloridx]

    for h in range(24):
        for w in range(32):
            sensorout.set_at((w, h), pixels[h * 32 + w])

    img = Image.new("RGB", (32, 24))
    img.putdata(pixels)
    if not args.disable_interpolation:
        img = img.resize((32 * INTERPOLATE, 24 * INTERPOLATE), Image.BICUBIC)
    img_surface = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
    scaled_surface = pygame.transform.scale(img_surface.convert(), screen.get_size())
    screen.blit(scaled_surface, (0, 0))
    pygame.display.update()
    pygame.event.pump()

    # 저장 모드가 활성화되어 있다면 현재 프레임을 저장합니다.
    if saving_mode:
        filename = os.path.join(save_folder, f"laydown{screenshot_count}.png")
        pygame.image.save(pygame.display.get_surface(), filename)
        print(f"Saved frame: {filename}")
        screenshot_count += 1
        if screenshot_count >= 5000:
            print("5000 screenshots captured. Exiting...")
            running = False

    end_time = time.monotonic()
    loop_time = end_time - start_time
    fps = 1.0 / loop_time if loop_time > 0 else 0
    print("Frame time: %0.2f s (%d FPS)" % (loop_time, fps))

pygame.quit()

