# import numpy as np
import vision_utils
import cv2
import threading

stop = False

server_mjpg = vision_utils.MJPG(None, threading.Lock())
server = vision_utils.MJPGserver(server_mjpg)

# noinspection PyArgumentList
cap = cv2.VideoCapture(0)
rval, _ = cap.read()

server.start()

try:
    while rval:
        rval, frame = cap.read()

        frame = cv2.flip(frame, 1)

        server_mjpg.lock.acquire()
        server_mjpg.frame = cv2.imencode(".jpg", frame)[1].tostring()
        server_mjpg.lock.release()
except KeyboardInterrupt:
    server.stop()
