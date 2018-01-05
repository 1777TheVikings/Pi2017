from PIL import ImageGrab
import numpy as np
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

x_offset = 1366 - 320 - 25
y_offset = 786 - 180 - 25

while rval:
    rval, frame_webcam = cap.read()  # 720x1280 for MacBook webcam
    frame_webcam = cv2.resize(frame_webcam, (0, 0), fx=0.25, fy=0.25)  # 180x320 after resize

    frame = np.array(ImageGrab.grab(bbox=(0, 0, 1365, 785)))  # 1366x786 for MacBook display
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    cv2.putText(frame, "Viewer Count: " + str(vision_utils.VIEWER_COUNT), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2,
                (255, 255, 255))
    frame[y_offset:y_offset + frame_webcam.shape[0], x_offset:x_offset + frame_webcam.shape[1]] = frame_webcam

    frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

    server_mjpg.lock.acquire()
    server_mjpg.frame = cv2.imencode(".jpg", frame)[1].tostring()
    server_mjpg.lock.release()
