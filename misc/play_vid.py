import sys

import numpy as np
import cv2

while True:
    cap = cv2.VideoCapture(sys.argv[1])
    while True:
        flag, frame = cap.read()
        if not flag:
            break
        if cv2.waitKey(10) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            sys.exit()
        cv2.imshow('frame', frame)

