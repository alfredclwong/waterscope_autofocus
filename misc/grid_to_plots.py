from __future__ import print_function

import sys, glob, re

import scipy.misc
import scipy.ndimage as sn
import scipy.signal as ssig
import scipy.stats as sstat
import numpy as np

directory = '/home/alfred/waterscope/images/grid-sweep/'

#'''
# Take cmd-line args (which pixel to read)
if len(sys.argv) < 3:
    sys.exit(-1)
x = int(sys.argv[1])
y = int(sys.argv[2])
#'''

# Save data points in the following lists
zs = []
fms = []

# Iterate through files
for infile in glob.glob("".join([directory, 'z*.png'])):
    # Read image
    image = scipy.misc.imread(infile)

    # Store data point for plot
    zs.append(int(re.search(r'\d+', infile).group())) # extracts int from str
    fms.append(image[y, x]) # extracts pixel form img

# Sort lists (glob doesn't order)
fms = [fms for _, fms in sorted(zip(zs, fms))]
zs = sorted(zs)

# Apply filter
#fms = ssig.medfilt(fms, 11)

# Display data
print('plot(', end='')
print(zs, end=',')
print(fms, end=')\n')

print(sstat.tstd(fms))
#print(sstat.kurtosis(fms))
