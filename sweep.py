"""autofocus.py

todo: round input res up to nearest 32/16/8(?)
todo: script + transistor for resetting arduino
todo: fix reverse sweep start pos bug
"""
from __future__ import print_function
import time
import threading

import smbus
import numpy as np
import scipy.ndimage as sn
import picamera


# I2C
bus = smbus.SMBus(1)
address = 0x04

timeout = 100
secperdeg = 0.005
res = (640, 480)
#import sys
#res = (int(sys.argv[1]), int(sys.argv[2]))

def move(angle):
    """Communicate an angle to to the Arduino using I2C which will in turn
    move the servo to the position specified.
    """
    #Since the servo's range of motion is less than 180 degrees, we can always
    # contain the data within one byte.
    bus.write_byte(address, angle)

class FocusMeasureProcessor(threading.Thread):
    """This class is a thread that receives images and calculates focus
    measures for them.
    """
    def __init__(self, owner, resolution, mask=None):
        # Set up thread.
        super(FocusMeasureProcessor, self).__init__()
        self.event = threading.Event()
        self.terminated = False
        self.owner = owner

        # Declare members required for image processing (is this necessary?).
        self.image = np.empty(resolution[::-1], dtype=np.uint8)
        self.angle_index = -1

        # Default mask is all 1s (unmasked).
        if mask is None:
            self.mask = np.ones(resolution[::-1], dtype=bool)
        else:
            self.mask = mask

        # Start thread.
        self.start()

    def run(self):
        # This code loops in a separate thread.
        while not self.terminated:
            # Wait for an image to be received.
            if self.event.wait(1):
                # Calculate focus measure, applying mask after laplace
                # transform.
                image_laplace = sn.filters.laplace(self.image)
                focus_measure = np.mean(image_laplace[self.mask])

                # Write to corresponding position in owner's focus_measure
                # array.
                self.owner.focus_measures[self.angle_index] = focus_measure

                # Done. Reset event and return to pool.
                self.event.clear()
                with self.owner.lock:
                    self.owner.pool.append(self)

class Sweeper(object):
    """This class sweeps the servo through a range of positions, pulling
    frames from a video stream at appropriate times and delegating them
    amongst processing threads to construct an array of focus_measures for
    each position.
    """
    def __init__(self, angles, resolution, mask=None, threads=4):
        # Flag for communicating with 'outsiders' that sweeping is done.
        self.done = False

        # Construct a pool of processors along with a lock to control access
        # between threads.
        self.threads = threads
        self.resolution = resolution
        self.pixels = np.prod(resolution)
        self.lock = threading.Lock()
        self.pool = [
                FocusMeasureProcessor(self, resolution, mask) \
                for i in range(threads)]
        self.processor = None

        # Sweeper-specific members
        self.angles = angles
        self.angle_index = 0
        self.focus_measures = [None] * len(angles)

        # We don't want to process a new frame until the servo has moved to
        # the correct position, so use this parameter to stall.
        self.next_frame = time.time() # servo is already in position

    def write(self, buf):
        # This is called for every frame of video capture.
        # We are only interested in the frames where the servo is not moving
        if time.time() > self.next_frame:
            # Set the current processor going.
            if self.processor:
                # Send frame to processor
                self.processor.image = np.frombuffer(
                        buf, dtype=np.uint8, count=self.pixels).reshape(
                        self.resolution[1], self.resolution[0])
                self.processor.angle_index = self.angle_index

                # Signal to start processing
                self.processor.event.set()

                # Move servo to next position - unless we are at the end of
                # the range in which case begin termination.
                if self.angle_index == len(self.angles) - 1:
                    self.done = True
                else:
                    self.angle_index += 1
                    move(self.angles[self.angle_index])

                    # Allow time for movement to complete before processing
                    # next frame:
                    # 0.01s per degree moved.
                    self.next_frame = (
                            time.time()
                            + secperdeg
                            * (self.angles[self.angle_index]
                            - self.angles[self.angle_index - 1]))

            # Attempt to grab a spare processor for the next frame.
            with self.lock:
                if self.pool:
                    self.processor = self.pool.pop()
                else:
                    # No processors available. By assigning None to
                    # self.processor we make Sweeper skip frames until
                    # a processor becomes available. In the meantime no move()
                    # calls are made so nothing is lost (except time).
                    self.processor = None

    def flush(self):
        # Called when video recording ends.
        # Need to stop threads in an orderly fashion.
        # First add the current processor back to the pool.
        if self.processor:
            with self.lock:
                self.pool.append(self.processor)
                self.processor = None

        # Now empty the pool, joining each thread as we go
        target_threads = threading.active_count() - self.threads
        while threading.active_count() > target_threads: # still not foolproof
            with self.lock:
                try:
                    proc = self.pool.pop()
                    proc.terminated = True
                    proc.join()
                except IndexError:
                    pass # pool empty

def sweep(angles, camera, resolution, framerate = 30):
    """Sweep the servo through a range of angles, evaluating a focus measure
    for each one from images captured at the given resolution.

    Aim for moving through the array of angles at a rate specified by
    framerate parameter.

    Return an array of focus measures corresponding to each position.
    """
    # Move servo to starting position.
    move(angles[0])

    # Set camera resolution.
    camera.sensor_mode = 4 # full field of view capture
    camera.resolution = resolution

    # Start camera and give it time to adjust to light levels.
    camera.start_preview()
    camera.exposure_mode = 'auto'
    camera.awb_mode = 'auto'
    time.sleep(2)

    # Now that camera is calibrated, fix its settings.
    # Shutter speed
    camera.shutter_speed = camera.exposure_speed
    camera.exposure_mode = 'off'
 
    # White balance
    g = camera.awb_gains
    camera.awb_mode = 'off'
    camera.awb_gains = g

    # Start a video recording which will allow us to rapidly capture and
    # process frames.
    camera.framerate = framerate
    sweeper = Sweeper(angles, resolution)
    camera.start_recording(sweeper, 'yuv')

    # Wait until sweeper is finished.
    start = time.time()
    while time.time() - start < timeout and not sweeper.done:
        camera.wait_recording(1.0 / framerate)
    camera.stop_recording()
    camera.stop_preview()

    # Sweep finished. Return calculated focus measures.
    return sweeper.focus_measures

def main():
    with picamera.PiCamera() as camera:
        for i in range(1, 8, 2):
            print(',angles,')
            fms = sweep(range(5, 151, 5), camera, (64*i, 48*i))
            fms -= np.amin(fms, axis=0)
            fms /= np.amax(fms, axis=0)
            fms += i - 1
            print(fms.tolist())
            print(',angles,')
            fms = sweep(range(5, 151, 5), camera, (64*(i+1), 48*(i+1)))
            fms -= np.amin(fms, axis=0)
            fms /= np.amax(fms, axis=0)
            fms += i
            print(fms.tolist())

if __name__ == "__main__":
    main()
