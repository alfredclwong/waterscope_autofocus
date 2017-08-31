#waterscope_autofocus

#autofocus.ini
config file to be read with argparser lib

#autofocus.py
sweep full range and move to position with max fm

#calibrate_cam.py
let picamera auto adjust exposure and awb for 2 seconds

#focal_stack.py
align stack of images and take best focused pixels to construct a super-image

#make_mask.py
generate simple masks for autofocus

#mask.png
make_mask.py output. current autofocus mask

#move.py
move servo manually

#start.txt/stop.txt
from running web interface's start.sh/stop.sh in this directory

#sweep.h264
video_sweep output. for analysis

#sweep.py
sweep through a given range, using multiple threads to process images captured

#video_sweep.py
quickly record a sweep with no processing
