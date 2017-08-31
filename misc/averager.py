"""averager.py

Copied from 
https://stackoverflow.com/questions/17291455/how-to-get-an-average-picture-from-100-pictures-using-pil
Adapted slightly to easily change directory and extension.

This script will read all files from the specified directory which have names
ending with any of the strings specified in the list 'extensions'. Then it
will save an averaged image in the same directory.

Parameters can either be changed in the following code or through command-line
arguments:

    python averager.py [directory] [extension1] [extension2] ...

    python averager.py /home/pi/images/ .png .PNG .jpg .JPG

NOTE: code assums that extensions are 4 characters long and images are RGB.
"""

from __future__ import print_function
import os, numpy, PIL, sys
from PIL import Image


# Adjustable parameters - os.getcwd() returns the current working directory
directory = os.getcwd()
extensions = [".png", ".PNG"] # WARNING: extensions must be 4 characters long

# Optionally adjust parameters with command-line arguments
if len(sys.argv) > 1:
    # Read first cmd-line arg as directory param
    directory = sys.argv[1]

    # Read all remaining as extensions
    if len(sys.argv) > 2:
        # Overwrite default extensions
        extensions = []

        # Record new extensions
        for extension in sys.argv[2:]:
            extensions.append(extension)

print("reading images from %s\nlooking for extensions "% directory, end='')
print(extensions)

# Access all PNG files in directory
allfiles=os.listdir(directory)
imlist=["".join([directory, filename]) for filename in allfiles if filename[-4:] in extensions]

# Exit with error message if no images found
if len(imlist) == 0:
    print("error: no images found in %s" % directory)
    sys.exit(-1)

# Assuming all images are the same size, get dimensions of first image
w,h=Image.open(imlist[0]).size
N=len(imlist)

# Create a numpy array of floats to store the average (assume RGB images)
arr=numpy.zeros((h,w,3),numpy.float)

# Build up average pixel intensities, casting each image as an array of floats
for im in imlist:
    imarr=numpy.array(Image.open(im),dtype=numpy.float)
    arr=arr+imarr/N

# Round values in array and cast as 8-bit integer
arr=numpy.array(numpy.round(arr),dtype=numpy.uint8)

# Generate, save and preview final image
out=Image.fromarray(arr,mode="RGB")
outfile = "".join([directory, "average", extensions[0]])
out.save(outfile)
print("averaged image saved to %s" % outfile)
#out.show()
