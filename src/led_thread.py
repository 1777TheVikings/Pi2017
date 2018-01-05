import RPi.GPIO as GPIO
import threading
import time
import os


def toggleLED(ledStatus):
    if ledStatus == "on":
        GPIO.output(16, GPIO.HIGH)
        return "off"
    elif ledStatus == "off":
        GPIO.output(16, GPIO.LOW)
        return "on"
    else:
        raise ValueError("ledStatus is set to an invalid value: " + ledStatus)


def slowBlink(ledStatus):
    newStatus = toggleLED(ledStatus)
    time.sleep(.25)
    return newStatus


def fastBlink(ledStatus):
    newStatus = toggleLED(ledStatus)
    time.sleep(0.125)
    return newStatus


functionStates = {"slow": slowBlink, "fast": fastBlink}

GPIO.setmode(GPIO.BCM)
GPIO.setup(16, GPIO.OUT)
GPIO.output(16, GPIO.HIGH)


class ledThread(threading.Thread):
    def __init__(self, threadID, name, state, ledStatus):
        super(ledThread, self).__init__()
        self.threadID = threadID
        self.name = name
        self.state = state
        self.ledStatus = ledStatus
        
        self._stop_event = threading.Event()
    
    def stop(self):
        self._stop_event.set()
    
    def stopped(self):
        return self._stop_event.is_set()
    
    def run(self):
        while 1:
            if self.stopped():
                self.state == "finished"
            print self.ledStatus
            if self.state == "finished":
                GPIO.output(16, GPIO.HIGH)
                break
            elif self.state == "solid":
                GPIO.output(16, GPIO.LOW)
                time.sleep(0.1)
                continue
            funcToExec = functionStates[self.state]
            self.ledStatus = funcToExec(self.ledStatus)


if __name__ == "__main__":
    t1 = ledThread(1, "LED-thread", "solid", "on")
    t1.daemon = True
    t1.start()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print "ok"
        t1.stop()
        t1.join()
