import cv2


class ContourInfo(object):
    def __init__(self, contours, focal_length):
        self._contours = contours
        self._focal_length = focal_length
        self.calculate()

    def calculate(self):
        centers = find_center_of_contours(self._contours)
        dist_strips = sqrt( ((centers[1][0] - centers[0][0]) ** 2) + \
                            ((centers[1][1] - centers[0][1]) ** 2) )
        self.midpoint = ( ((centers[0][0] + centers[1][0]) / 2), \
                          ((centers[0][1] + centers[1][1]) / 2) )
        self.dist_away = find_distance(dist_strips, self._focal_length)
        if midpoint[0] < 320:
            self.angle = DEGREES_PER_PIXEL * (320 - midpoint[0])
        else:
            self.angle = -1 * (DEGREES_PER_PIXEL * (midpoint[0] - 320))


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


def calculate_focal_length(contours):
    """ Calculates the focal length of the camera based on two
        contours located a known distance apart.

        Takes a list of two contours and returns a float
        indicating the focal length.
    """
    centers = find_center_of_contours(contours)
    distance = sqrt( ((centers[1][0] - centers[0][0]) ** 2) + \
                     ((centers[1][1] - centers[0][1]) ** 2) )
    return ( distance * CALIB_DIST ) / DIST_BETWEEN_STRIPS
