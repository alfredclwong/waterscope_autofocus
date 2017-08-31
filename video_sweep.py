import time
import math

import picamera

import sweep

angles = range(6, 177, 5)

sweep.move(angles[0])

with picamera.PiCamera() as camera:
    #camera.sensor_mode = 2
    camera.resolution = (1296,972)
    camera.exposure_mode = 'auto'
    camera.awb_mode = 'auto'
    camera.start_preview()
    time.sleep(2)
    camera.shutter_speed = camera.exposure_speed
    camera.exposure_mode = 'off'
    g = camera.awb_gains
    camera.awb_mode = 'off'
    camera.awb_gains = g
    camera.framerate = 40
    camera.start_recording('sweep.h264')
    for angle in angles:
        sweep.move(angle)
        camera.wait_recording(0.1)
    camera.stop_recording()
