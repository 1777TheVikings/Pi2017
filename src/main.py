import cv2
import numpy
import pipeline
import os
import sys
from math import sqrt

# maximum vertical variance between pairs of viable keypoints
MAX_Y_VARIANCE = 25

# approx. distance between center of two strips of tape, in inches
DISTANCE_BETWEEN_STRIPS = 8.5


# focal length only works for 480x360
#                (distance between strips in px. * distance from camera in in.)
# focal_length = --------------------------------------------------------------
#                                 distance between strips in in.
focal_length = (88 * 36) / DISTANCE_BETWEEN_STRIPS


# ensures that the Pi Camera drivers are loaded
os.system("sudo modprobe bcm2835-v4l2 #")

cam = cv2.VideoCapture(0)
print "[INFO] Video capture started"

if cam.isOpened(): # attempts to get first frame 
    rval, frame = cam.read()
    print "[INFO] Test frame rval success"
else:
    rval = False
    print "[ERROR] Test frame rval fail"

# GRIP pipeline object
pl = pipeline.GripPipeline()

try:
    while rval:
        rval, frame = cam.read()
        
        pl.process(frame)
        # pl.process does not return the end image; instead, results are stored in
        # the pipeline object (e.g. pl.find_blobs_output)
        output = pl.find_blobs_output

        viable_pairs = []        
        if len(output) >= 2:
            for i in output:
                output.remove(i)
                for j in output:
                    if j.pt[1] - 10 <= i.pt[1] and j.pt[1] + 10 >= i.pt[1]:
                        output.remove(j)
                        viable_pairs.append([(int(i.pt[0]), int(i.pt[1])), (int(j.pt[0]), int(i.pt[1]))])
        
        data = []
        for i in viable_pairs:
            midpoint = (((i[0][0] + i[1][0]) / 2), ((i[0][1] + i[1][1]) / 2))
            distance = sqrt(((i[1][0] - i[0][0]) ** 2) + ((i[1][1] - i[0][1]) ** 2))
            data.append([midpoint, (DISTANCE_BETWEEN_STRIPS * focal_length) / distance])
        
        print data\

except KeyboardInterrupt:
    print "\n[INFO] Received KeyboardInterrupt; exiting"
finally: # always release video capture
    print "[INFO] Releasing video capture"
    cam.release()
