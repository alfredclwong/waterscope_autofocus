from __future__ import print_function
import sweep
import picamera

import scipy.signal

# sweep and move to max fm angle
with picamera.PiCamera() as camera:
    angles = range(1, 159, 1)
    fms = sweep.sweep(angles, camera, (640, 480))
max_angle = angles[fms.index(max(scipy.signal.medfilt(fms)))]
sweep.move(max_angle)
print('autofocused at %d degrees' % max_angle)

# Output for Octave
#print('angles = ', end='')
#print(angles)
#print('fms = ', end='')
#print(fms)
#print('plot(angles, fms)')

#scipy.stats.medfilt(fms)

print('plot(', end='')
print(angles, end=',')
print(fms, end=')\n')

print('plot(', end='')
print(angles, end=',')
print(scipy.signal.medfilt(fms).tolist(), end=')\n')
