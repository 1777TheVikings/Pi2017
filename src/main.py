from math import sqrt
from networktables import NetworkTables
import vision_utils
import cv2
import os
import pipeline
import numpy
import sys
import threading
import time


frame = None
rval = None


# if true, outputs to console instead of NetworkTables
# set this using "-t" instead of manually setting this
TEST_OUTPUT = False
# if true, use status (SD card usage) LED to indicate status
# diable using "--no-led" instead of manually setting this
LED_STATUS = True
# if true, create an MJPG stream to be used by SmartDashboard
# set this using "-s" instead of manually setting this
STREAM_VIDEO = False
# If true, record a video of the stream sent to the driver
# station. Disable using "--no-rec" instaed of manually
# setting this. See the readme in ../rec for more info.
RECORD_STREAM = True
# absolute path to a calibration image
CALIB_IMG_PATH = "/home/pi/Pi2017/img/3feet.jpg"
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


def led_on():
    os.system("sudo echo 1 > /sys/class/leds/led0/brightness")


def led_off():
    os.system("sudo echo 0 > /sys/class/leds/led0/brightness")


if __name__ == "__main__":
    try:
        if "-t" in sys.argv[1:]:
            TEST_OUTPUT = True
        if "-s" in sys.argv[1:]:
            STREAM_VIDEO = True
        if "--no-led" in sys.argv[1:]:
            LED_STATUS = False
        if "--no-rec" in sys.argv[1:]:
            RECORD_STREAM = False
    except IndexError:
        pass
       
    if LED_STATUS:
        # prepare status LED for use by disabling normal behavior
        if LED_STATUS:
            print "[INFO] Disabling normal status LED behavior"
            os.system("sudo echo none > /sys/class/leds/led0/trigger")
            led_off()
    
    if not TEST_OUTPUT:
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
    
    if not TEST_OUTPUT:
        if not sd.isConnected():
            print "[INFO] Waiting for NetworkTables connection..."
            while not sd.isConnected():
                pass
        print "[INFO] NetworkTables ready"
    
    if LED_STATUS:
        led_on()
    
    if STREAM_VIDEO:
        print "[INFO] Starting video stream..."
        server_mjpg = vision_utils.MJPG(None, threading.Lock())
        server = vision_utils.MJPGserver(server_mjpg)
        server.start()
    
    if RECORD_STREAM:
        stream_width = 480
        stream_height = 640
        print "[INFO] Starting recording"
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter('last.mjpg', fourcc, 30.0, (640, 480))
    
    print "[INFO] Starting detection"
    
    frame_num = 1
    try:
        while rval:
            vision_utils.start_time("reading")
            rval, frame = cam.read()
            vision_utils.end_time("reading")
            
            vision_utils.start_time("processing.grip")
            pl.process(frame)
            vision_utils.end_time("processing.grip")
            vision_utils.start_time("processing.matcher")
            # pl.process does not return the end image; instead, results are
            # stored in the pipeline object (e.g. pl.find_contours_output)
            pl_out = pl.convex_hulls_output
            if len(pl_out) > 1:
                contour_info = vision_utils.ContourInfo(pl_out, focal_length)
                if TEST_OUTPUT:
                    print "angle = " + str(contour_info.angle) + \
                          "; distance = " + str(contour_info.dist_away) + \
                          "; frame = " + str(frame_num)
                else:
                    sd.putNumber('pi_angle', contour_info.angle)
                    sd.putNumber('pi_distance', contour_info.dist_away)
                    sd.putNumber('pi_frame', frame_num)
                frame_num += 1
            vision_utils.end_time("processing.matcher")
            
            if STREAM_VIDEO:
                vision_utils.start_time("resize+encode")
                frame_width, frame_height, _ = frame.shape
                stream_frame = cv2.resize(frame,
                                          None,
                                          fx=frame_width / stream_width,
                                          fy=frame_height / stream_height,
                                          interpolation=cv2.INTER_CUBIC)
                
                server_mjpg.lock.acquire()
                server_mjpg.frame = cv2.imencode(".jpg", frame)[1].tostring()
                server_mjpg.lock.release()
                vision_utils.end_time("resize+encode")
            
            if RECORD_STREAM:
                vision_utils.start_time("recording")
                out.write(frame)
                vision_utils.end_time("recording")
    
            
    except KeyboardInterrupt:
        print "\n[INFO] Received KeyboardInterrupt; exiting"
        vision_utils.report()
    finally:
        print "[INFO] Releasing video capture"
        cam.release()
        out.release()
        if STREAM_VIDEO:
            print "[INFO] Shutting off video stream"
            server.stop()

