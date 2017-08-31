from __future__ import print_function
import time

import picamera

with picamera.PiCamera() as camera:
    camera.exposure_mode = 'auto'
    camera.awb_mode = 'auto'
    camera.start_preview()
    time.sleep(2)
    camera.shutter_speed = camera.exposure_speed
    camera.exposure_mode = 'off'
    g = camera.awb_gains
    camera.awb_mode = 'off'
    camera.awb_gains = g

    print('shutter speed %d' % camera.exposure_speed)
    print('awb_gains', end='')
    print(g)
