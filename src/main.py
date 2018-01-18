from math import sqrt
from networktables import NetworkTables
from constants import *
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


# load Pi Camera drivers
os.system("sudo modprobe bcm2835-v4l2 #")


pl = pipeline.GripPipeline()


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
    focal_length = vision_utils.calculate_focal_length(cnt)
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
        stream_width = 480
        stream_height = 640
        print "[INFO] Starting video stream..."
        server_mjpg = vision_utils.MJPG(None, threading.Lock())
        server = vision_utils.MJPGserver(server_mjpg)
        server.start()
    
    if RECORD_STREAM:
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

