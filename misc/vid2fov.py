import sys
import time
import os

import cv2
import numpy as np
import scipy.signal as ssig
from statsmodels import robust as smrobust

# Read frames from file
path = sys.argv[1]
cap = cv2.VideoCapture(path)

# Get video properties
# resolution
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# number of frames (.h264 not supported - manual counting)
frame_count = 0 # set to n != 0 to only read first n frames of video
if frame_count == 0:
    while True:
        # Read frame - returns False to flag if failed
        flag, _ = cap.read()

        if not flag: # end of video
            # Reset video reader
            cap = cv2.VideoCapture(path)
            break

        # Count frame
        frame_count += 1
        print("counting frames: %d" % frame_count, end='\r')
    print()
else:
    print("only reading first %d frames" % frame_count)

# Create grids
grid_size = 8
gridxs = range(0, width, grid_size)
gridys = range(0, height, grid_size)

# Initialise data storage structures
#fms = np.empty(frame_count)
max_fm = -100
max_fm_num = -1
grids = np.empty((frame_count, len(gridys), len(gridxs)))

# Keep a record of the sharpest frame
sharpest = np.empty((width, height))

# Iterate through frames
for frame_num in range(frame_count):
    # Read frame
    _, frame = cap.read()

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply Laplace transform to whole image
    lap = cv2.Laplacian(frame, cv2.CV_64F)
    
    # Calculate overall fm (variance of laplace)
    fm = np.var(lap)

    # Check to see if we have a new sharpest frame
    if fm > max_fm:
        max_fm = fm
        max_fm_num = frame_num
        sharpest = frame
    
    # Calculate grid fms
    for y in range(len(gridys)-1):
        for x in range(len(gridxs)-1):
            grids[frame_num, y, x] = lap[
                    gridys[y]:gridys[y+1],
                    gridxs[x]:gridxs[x+1]].var()
    
    # Output progress - this can take a while!
    #print("processing frame %d/%d (%d%%)" % (
    print("processing frames {:d}/{:d} ({:.0%})".format(
        frame_num + 1,
        frame_count,
        (frame_num + 1) / frame_count), end='\r')

# Done with video
cap.release()

# Avoid carriage return (/r) overwrite and output sharpest frame number
print("\nsharpest frame was %d/%d" % (max_fm_num, frame_count))

# Filter noise
#fms = ssig.medfilt(fms)
grids = ssig.medfilt(grids)

# Normalise across each grid pixel. Temporarily ignore divide by 0 errors.
with np.errstate(invalid='ignore'):
    grids = (grids - np.amin(grids, axis=0)) / np.ptp(grids, axis=0)

# Initialise fov mask
fov = np.zeros((height, width), dtype=np.bool)
while True:
    # Loop through varying thresholds
    for thresh in range(15, 25, 1):

        for y in range(len(gridys)):
            for x in range(len(gridxs)):
                # Analyse curve shape for this grid pixel
                curve = grids[:,y,x]
                
                # MAD (median absolute deviation) sums the absolute difference
                # of each value from the median and divides this by N
                s = smrobust.mad(curve)

                # Apply threshold to generate an FoV mask
                if s > thresh / 100:
                    fov[
                            y*grid_size : (y+1) * grid_size,
                            x*grid_size : (x+1) * grid_size] = True
                else:
                    fov[
                            y*grid_size : (y+1) * grid_size,
                            x*grid_size : (x+1) * grid_size] = False

        ## Use morphological transforms to clean up mask
        ker = np.ones((grid_size * 2, grid_size * 2))
        # cv2 morph functions work with images. bool mask to grayscale:
        fov_morphed = np.array(fov * 255, dtype=np.uint8)
        # Initial erode gets rid of small specks outside fov
        fov_morphed = cv2.erode(fov_morphed, ker, iterations=1)
        # Double dilate to remove medium specks inside fov
        fov_morphed = cv2.dilate(fov_morphed, ker, iterations=3)
        # Erode to restore to roughly original area
        fov_morphed = cv2.erode(fov_morphed, ker, iterations=1)
    
        # cv2 contours allow us to outline shapes generated and get centres
        cnts = cv2.findContours(
                fov_morphed,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[1] # some kinda cv2/cv3 peculiarity

        ## Now we have all the info to construct our fov image
        sharpCopy = np.array(sharpest) # copy values explicitly
        # Black out parts outside of the fov
        sharpCopy[np.invert(fov_morphed.astype(bool))] = 0
        # Get largest contour
        largest_cnt = cnts[0]
        for c in cnts:
            if cv2.contourArea(c) > cv2.contourArea(largest_cnt):
                largest_cnt = c
        
        # Draw largest contour and its centre
        M = cv2.moments(largest_cnt)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        cv2.drawContours(sharpCopy, [largest_cnt], -1, (255, 0, 255), 2)
        cv2.circle(sharpCopy, (cX, cY), 7, (255,0,255), -1)
    
        # Display current threshold value
        cv2.putText(
                sharpCopy,
                "threshold: {:.2f}".format(thresh / 100),
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,255))

        # Display % coverage of fov
        cv2.putText(
                sharpCopy,
                "fov coverage: {:.1%}".format(
                    cv2.contourArea(largest_cnt) / width / height),
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,255))
        
        # Display image
        cv2.imshow('fov', sharpCopy)

        # Save image
        vid_name, _ = os.path.splitext(path)
        cv2.imwrite("%s-%d.png" % (vid_name, thresh), sharpCopy) 

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            sys.exit()
