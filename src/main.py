import cv2
import numpy
import pipeline
import os
import sys
from math import sqrt


# ensures that the Pi Camera drivers are loaded
os.system("sudo modprobe bcm2835-v4l2 #")
# GRIP pipeline object
pl = pipeline.GripPipeline()

# maximum vertical variance between pairs of viable keypoints
MAX_Y_VARIANCE = 25
# maximum diameter variance between pairs of viable keypoints
MAX_DIAMETER_VARIANCE = 20
# maximum variance between the ratio of distance between two keypoints and
# the average diameter of the two keypoints
MAX_RATIO_VARIANCE = 50
# approx. distance between center of two strips of tape, in inches
DIST_BETWEEN_STRIPS = 8.5
# relative path to a calibration image
CALIB_IMG_PATH = "../img/3feet.jpg"
# distance between camera and peg in the calibration image, in inches
CALIB_DIST = 36


def find_viable_pairs(blobs, distanceDiameterMulti=False, allowMultiPairing=True):
    """ Finds pairs of blobs within the image that could potentially be the peg,
        with closer (further apart) pairs being listed first.
        
        Arguments:
            blobs - A list of keypoint objects, preferrably from pl.find_blobs_output
            distanceDiameterMulti - A float specifying the following multiplier:
            
        average diameter of keypoints * distanceDiameterMulti = distance between keypoints
            
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
            if not ( j.pt[1] - MAX_Y_VARIANCE <= i.pt[1] and j.pt[1] + MAX_Y_VARIANCE >= i.pt[1] ):
                continue
            if not ( abs(i.size - j.size) <= MAX_DIAMETER_VARIANCE):
                continue
            if distanceDiameterMulti:
                d = sqrt( ((i[1].pt[0] - i[0].pt[0]) ** 2) + \
                          ((i[1].pt[1] - i[0].pt[1]) ** 2) )
                avgDia = (( i.size + j.size ) / 2)
                if not (dist / avgDia) - MAX_RATIO_VARIANCE <= distanceDiameterMulti and \
                       (dist / avgDia) + MAX_RATIO_VARIANCE >= distanceDiameterMulti:
                    continue
                
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


def find_distance(dist, focal_len):
    return ( DIST_BETWEEN_STRIPS * focal_len ) / dist


# Automatic calibration for distance detection
# focal length only works for 480x360
#
#                (distance between strips in px. * distance from camera in in.)
# focal_length = --------------------------------------------------------------
#                                 distance between strips in in.

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
    # focal length calculation used by find_distance()
    focal_length = ( kp[2] * CALIB_DIST ) / DIST_BETWEEN_STRIPS
    # multiplier for "distanceDiameterMulti" argiment of find_distance()
    ddMulti = kp[2] / (( kp[0].size + kp[1].size ) / 2)
    
    
    cam = cv2.VideoCapture(0)
    print "[INFO] Video capture started"
    
    if cam.isOpened(): # attempts to get first frame 
        rval, frame = cam.read()
        print "[INFO] Test frame rval success"
    else:
        rval = False
        print "[ERROR] Test frame rval fail"
    
    try:
        while rval:
            rval, frame = cam.read()
            
            pl.process(frame)
            # pl.process does not return the end image; instead, results are stored in
            # the pipeline object (e.g. pl.find_blobs_output)
            output = pl.find_blobs_output
            viable_points = find_viable_pairs(output, ddMulti)
            
            for i in viable_points:
                print find_distance(i[2], focal_length)
    
    except KeyboardInterrupt:
        print "\n[INFO] Received KeyboardInterrupt; exiting"
    finally: # always release video capture
        print "[INFO] Releasing video capture"
        cam.release()

