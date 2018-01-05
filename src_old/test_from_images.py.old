import cv2
import numpy
import pipeline
import os
import sys
from math import sqrt
from main import *


# ensures that the Pi Camera drivers are loaded
os.system("sudo modprobe bcm2835-v4l2 #")
# GRIP pipeline object
pl = pipeline.GripPipeline()

# list of relative image paths
IMAGE_PATHS = ["../img/test_images/1.jpg", "../img/test_images/2.jpg", "../img/test_images/3.jpg"]
# maximum vertical variance between pairs of viable keypoints
MAX_Y_VARIANCE = 25
# approx. distance between center of two strips of tape, in inches
DIST_BETWEEN_STRIPS = 8.5
# relative path to a calibration image
CALIB_IMG_PATH = "../img/3feet.jpg"
# distance between camera and peg in the calibration image, in inches
CALIB_DIST = 36

if __name__ == "__main__":
    print "[INFO] Calculating focal length from test image"
    calibImg = cv2.imread(CALIB_IMG_PATH)
    if calibImg is None:
        print "[ERROR] Calibration image not found: " + CALIB_IMG_PATH
        exit()
    pl.process(calibImg)
    try:
        kp = find_viable_pairs(pl.find_blobs_output)[0]
    except IndexError:
        print "[ERROR] Calibration failed; no keypoint pairs found"
        exit()
    focal_length = ( kp[2] * CALIB_DIST ) / DIST_BETWEEN_STRIPS
    ddMulti = kp[2] / (( kp[0].size + kp[1].size ) / 2)
    
    for img in IMAGE_PATHS:
        print "[INFO] Processing image " + img
        frame = cv2.imread(img)
        pl.process(frame)
        # pl.process does not return the end image; instead, results are stored in
        # the pipeline object (e.g. pl.find_blobs_output)
        output = pl.find_blobs_output
        viable_points = find_viable_pairs(output, ddMulti)
        
        for i in viable_points:
            print find_distance(i[2], focal_length), i[0].pt, i[1].pt
