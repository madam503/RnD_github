"""
image_array was here!
"""

import board
import busio
import displayio
import time
import select
import RPi.GPIO as GPIO
from adafruit_ili9341 import ILI9341

external_expression_signal = None

class DisplayController:
    def __init__(self, gImage_idle_arr, gImage_gloomy_arr, gImage_blink_arr, gImage_happy_arr):

        self.idle_tilegrid = self.create_tilegrid_from_array(gImage_idle_arr)
        self.gloomy_tilegrid = self.create_tilegrid_from_array(gImage_gloomy_arr)
        self.blink_tilegrid = self.create_tilegrid_from_array(gImage_blink_arr)
        self.happy_tilegrid = self.create_tilegrid_from_array(gImage_happy_arr)
        self.current_tilegrid = self.idle_tilegrid
        
        GPIO.setmode(GPIO.BCM)
        LED_PIN = 18
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(LED_PIN, GPIO.HIGH)

        displayio.release_displays()
        spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)
        tft_cs = board.CE0
        tft_dc = board.D24
        display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs)
        self.display = ILI9341(display_bus, width=320, height=240)
        self.display.auto_refresh = False
        
        self.group = displayio.Group(scale=1)
        self.display.root_group = self.group
        self.group.append(self.current_tilegrid)
        self.display.refresh()
        
        self.last_blink_time = time.monotonic()
        self.last_input_time = None
        
        self.running = False
        
        
    def create_tilegrid_from_array(self, image_array):
        header = image_array[:8]
        IMAGE_WIDTH = header[2] | (header[3] << 8)
        IMAGE_HEIGHT = header[4] | (header[5] << 8)
        pixel_bytes = image_array[8:]
        expected_pixel_bytes = IMAGE_WIDTH * IMAGE_HEIGHT * 2  

        if len(pixel_bytes) < expected_pixel_bytes:
            raise ValueError("pixel data is empty.")

        bitmap = displayio.Bitmap(IMAGE_WIDTH, IMAGE_HEIGHT, 65536)

        for i in range(IMAGE_WIDTH * IMAGE_HEIGHT):
            byte_index = i * 2
            pixel_val = pixel_bytes[byte_index] | (pixel_bytes[byte_index + 1] << 8)
            x = i % IMAGE_WIDTH
            y = i // IMAGE_WIDTH
            bitmap[x, y] = pixel_val
        
        color_converter = displayio.ColorConverter()
        tile_grid = displayio.TileGrid(bitmap, pixel_shader=color_converter)
        tile_grid.x = 0
        tile_grid.y = (320 - IMAGE_HEIGHT) // 2
    
        return tile_grid

    def set_expression(self, expression):
        self.external_expression_signal = expression
        self.last_input_time = time.monotonic()

    def _process_external_signal(self):
        global external_expression_signal
        if external_expression_signal == "gloomy":
            self.current_tilegrid = gloomy_tilegrid
            print("[Emotion] current_tilegrid change >> gloomy")
            external_expression_signal = None
            if self.group:
                self.group.pop()
            self.group.append(self.current_tilegrid)
            self.display.refresh()
        elif external_expression_signal == "happy":
            self.current_tilegrid = happy_tilegrid
            print("[Emotion] current_tilegrid change >> happy")
            external_expression_signal = None
            if self.group:
                self.group.pop()
            self.group.append(self.current_tilegrid)
            self.display.refresh()

    def run(self):
        self.running = True
        while self.running:
            self._process_external_signal()
            
            if self.last_input_time is not None and time.monotonic() - self.last_input_time >= 6:
                if self.current_tilegrid != self.idle_tilegrid:
                    self.current_tilegrid = self.idle_tilegrid
                    if len(group) > 0:
                        group.pop()
                    self.group.append(self.current_tilegrid)
                    self.display.refresh()
                self.last_input_time = None

            now = time.monotonic()
            
            if now - self.last_blink_time >= 3:
                if len(self.group) > 0:
                    self.group.pop()
                self.group.append(self.blink_tilegrid)
                self.display.refresh()
                time.sleep(0.01)
                self.group.pop()
                self.group.append(self.current_tilegrid)
                self.display.refresh()
                self.last_blink_time = now

            time.sleep(0.01)
            
    def stop(self):
        self.running = False
        GPIO.cleanup()
def main():
    controller = DisplayController(gImage_idle_arr, gImage_gloomy_arr, gImage_blink_arr, gImage_happy_arr)
    global external_expression_signal
    print("[Emotion] Emotion module started")
    while True:
        if external_expression_signal is not None:
            print("[Emotion] Detected external_expression_signal =", external_expression_signal)
            _process_external_signal(external_expression_signal)
            external_expression_signal = None
            print("[Emotion] external_expression_signal reset to None.")
        time.sleep(0.1)
    
if __name__ == '__main__':
    main()