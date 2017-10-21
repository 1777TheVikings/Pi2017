import cv2
import numpy
import pipeline
import os
import sys
from math import sqrt


def find_viable_pairs(blobs, allowMultiPairing=True):
    """ Finds pairs of blobs within the image that could potentially be the peg,
        with closer (further apart) pairs being listed first.
        
        Arguments:
            blobs - A list of keypoint objects, preferrably from pl.find_blobs_output
            allowMultiPairing - A boolean that toggles whether a blob should be
                                allowed to be a part of several possible pairs.
                                Defaults to 'True'.
        
        Returns a list in this format:
        [ [blob 1,
           blob 2,
           distance between blobs as float,
           midpoint between blobs as KeyPoint object ], ...]
    """
    output = []
    if len(blobs) < 2:
        return []
    for i in blobs:
        blobs.remove(i)
        for j in blobs:
            if j.pt[1] - MAX_Y_VARIANCE <= i.pt[1] and j.pt[1] + 10 >= i.pt[1]:
                blobs.remove(j)
                output.append([i, j])
                if not allowMultiPairing:
                    break
    
    for i in output:
        dist = sqrt( ((i[1].pt[0] - i[0].pt[0]) ** 2) + \
                     ((i[1].pt[1] - i[0].pt[1]) ** 2) )
        i.append(int(dist))
        
        mp_coords = ( ((i[0].pt[0] + i[1].pt[0]) / 2), \
                      ((i[0].pt[1] + i[1].pt[1]) / 2) )
        mp = cv2.KeyPoint(mp_coords[0], mp_coords[1], 1)
        i.append(mp)
    
    return output


# maximum vertical variance between pairs of viable keypoints
MAX_Y_VARIANCE = 25

# approx. distance between center of two strips of tape, in inches
DISTANCE_BETWEEN_STRIPS = 8.5


# focal length only works for 480x360
#
#                (distance between strips in px. * distance from camera in in.)
# focal_length = --------------------------------------------------------------
#                                 distance between strips in in.
# cv2.imread("../img/3feet.jpg")


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
        viable_points = find_viable_pairs(output)
        
        print viable_points

except KeyboardInterrupt:
    print "\n[INFO] Received KeyboardInterrupt; exiting"
finally: # always release video capture
    print "[INFO] Releasing video capture"
    cam.release()
