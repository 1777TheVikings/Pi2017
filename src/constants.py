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