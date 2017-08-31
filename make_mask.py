"""make_mask.py

This script constructs a mask of 1s and 0s as specified by command-line
arguments and saves it as an image file.

The intention is for this mask to be applied to captured images to ignore
certain areas of the image.
"""

import sys
import ConfigParser

import numpy as np
import scipy.misc


# Default save path for the image
path = './'

# Default filename for the image
filename = 'mask'

# Default file format extension for the image
extension = '.png'

# Default resolution
resolution = (640, 480)


def draw_circle(array, a, b, r, val):
    """Draw a circle on array with centre (a, b) and radius r, filled with a
    given value (1s or 0s).
    """

    # We want to target all array[y, x] where (x-a)^2 + (y-b)^2 <= r*r. The
    # following code computes a grid of (x-a)^2 + (y-b)^2 values and then
    # compares it to r*r (constant) to get a boolean mask array.
    y, x = np.ogrid[-b : array.shape[0] - b, -a : array.shape[1] - a]
    mask = x*x + y*y <= r*r

    # Use mask to target desired circle within array. Write 0s if val is 0
    # and 1s otherwise.
    array[mask] = val != 0

def draw_rectangle(array, a, b, w, h, val):
    """Draw a rectangle on array with top-left corner (a, b), width w, and
    height h, filled with a given value (1s or 0s).
    """

    # Check to see if the rectangle described exceeds array's bounds and
    # change values accordingly.
    if a < 0:
        a = 0
    if b < 0:
        b = 0
    if a + w > array.shape[1]:
        w = array.shape[1] - a
    if b + h > array.shape[0]:
        h = array.shape[0] - b

    # Slice desired rectangle within array. Write 0s if val is 0 and 1s
    # otherwise.
    array[b : b + h, a : a + w] = val != 0


# Start off with a blank mask (all 1s so that image is entirely unmasked)
mask = np.ones(resolution[::-1], dtype=bool) # [::-1] reads tuple backwards

# Parse command-line arguments
for i, arg in enumerate(sys.argv):
    if arg == 'c':
        draw_circle(
                mask,
                int(sys.argv[i+1]),
                int(sys.argv[i+2]),
                int(sys.argv[i+3]),
                int(sys.argv[i+4]))
    elif arg == 'r':
        draw_rectangle(
                mask,
                int(sys.argv[i+1]),
                int(sys.argv[i+2]),
                int(sys.argv[i+3]),
                int(sys.argv[i+4]),
                int(sys.argv[i+5]))

# Save completed mask
scipy.misc.imsave("".join([path, filename, extension]), mask)

# For a viewable preview we want 1s to be whites (255) and 0s to be blacks (0)?
#scipy.misc.imsave("".join([path, filename, "-preview", extension]), mask * 255)
