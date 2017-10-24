from math import sqrt
from networktables import NetworkTables
import cv2
import os
import pipeline
import numpy


# relative path to a calibration image
CALIB_IMG_PATH = "../img/3feet.jpg"
# distance between strips, in inches
DIST_BETWEEN_STRIPS = 8.5
# distance between camera peg in the calibration image, in inches
CALIB_DIST = 36
# horizontal FoV / width of video
DEGREES_PER_PIXEL = 0.0971875


# load Pi Camera drivers
os.system("sudo modprobe bcm2835-v4l2 #")

pl = pipeline.GripPipeline()


def find_center_of_contours(contours):
    """ Takes a list of contours and returns the centroid
        (center point) of each one.
    """
    output = []
    for i in contours:
        m = cv2.moments(i)
        cx = int(m['m10']/m['m00'])
        cy = int(m['m01']/m['m00'])
        output.append((cx, cy))
    return output


def find_distance(dist, focal_len):
    """ Takes the distance between two strips and the focal
        length of the camera and returns the distance between
        the camera and the peg.
    """
    return ( DIST_BETWEEN_STRIPS * focal_len ) / dist


if __name__ == "__main__":
    print "[INFO] Connecting to NetworkTables"
    NetworkTables.initialize(server="roboRIO-1777-FRC.local")
    sd = NetworkTables.getTable("SmartDashboard")

    print "[INFO] Calculating focal length from test image"
    calibImg = cv2.imread(CALIB_IMG_PATH)
    if calibImg is None:
        print "[ERROR] Calibration imaage not found: " + CALIB_IMG_PATH
        exit()
    pl.process(calibImg)
    try:
        cnt = [pl.convex_hulls_output[0], pl.convex_hulls_output[1]]
    except IndexError:
        print "[ERROR] Calibration failed; did not find two convex hulls"
        exit()
    centers = find_center_of_contours(cnt)
    distance = sqrt( ((centers[1][0] - centers[0][0]) ** 2) + \
                     ((centers[1][1] - centers[0][1]) ** 2) )
    # focal length calculations used by find_distance()
    focal_length = ( distance * CALIB_DIST ) / DIST_BETWEEN_STRIPS
    print "[INFO] Calibration success; focal_length = " + str(focal_length)    
    
    
    cam = cv2.VideoCapture(0)
    print "[INFO] Attempting video capture start"
    
    if cam.isOpened():
        rval, _ = cam.read()
        if rval:
            print "[INFO] rval test success"
        else:
            print "[ERROR] rval test fail"
            exit()
    else:
        print "[ERROR] Video capture could not be opened"
    
    
    if not sd.isConnected():
        print "[INFO] Waiting for NetworkTables connection..."
        while not sd.isConnected():
            pass
    print "[INFO] NetworkTables ready"
    
    
    frame_num = 1
    try:
        while rval:
            rval, frame = cam.read()
            frame = cv2.flip(frame, 1)  # camera is upside down, so vertical flip
            
            pl.process(frame)
            # pl.process does not return the end image; instead, results are
            # stored in the pipeline object (e.g. pl.find_contours_output)
            pl_out = pl.convex_hulls_output
            if len(pl_out) > 1:
                centers = find_center_of_contours(pl_out)
                dist_strips = sqrt( ((centers[1][0] - centers[0][0]) ** 2) + \
                                    ((centers[1][1] - centers[0][1]) ** 2) )
                midpoint = ( ((centers[0][0] + centers[1][0]) / 2), \
                             ((centers[0][1] + centers[1][1]) / 2) )
                dist_away = find_distance(dist_strips, focal_length)
                if midpoint[0] < 320:
                    angle = DEGREES_PER_PIXEL * (320 - midpoint[0])
                else:
                    angle = -1 * (DEGREES_PER_PIXEL * (midpoint[0] - 320))
                sd.putNumber('angle', angle)
                sd.putNumber('distance', dist_away)
                sd.putNumber('frame', frame_num)
                frame += 1
            
    except KeyboardInterrupt:
        print "\n[INFO] Received KeyboardInterrupt; exiting"
    finally:
        print "[INFO] Releasing video capture"
        cam.release()
