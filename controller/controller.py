import serial
import time
import threading
from enum import IntEnum

class Command(IntEnum):
    STATUS = 0
    HEARTBEAT = 1
    MODE = 2
    SET_STEER = 3
    SET_THROTTLE = 4
    SET_CAMERA = 5
    SET_SPEED = 6
    SET_DIST = 7

class Mode(IntEnum):
    PASSTHROUGH = 0
    COMPUTER = 1
    COMPUTER_SC = 2
    LOST = 3

class ConnectionError(Exception):
    def __init__(self, device):
        self.message = "Connection error"
        self.device = device

class Controller:
    def __init__(self) -> None:
        self.connected = False
        self.port = None
        self.baudrate = None
        self.timeout = None
        self.arduino = None
        self.serial_lock = threading.Lock()
        self.written = 0
        self.write_flush = 1000

    def connect(self, port='COM3', baudrate=115200, timeout=.1):
        if not self.connected:
            self.port = port
            self.baudrate = baudrate
            self.timeout= timeout
            self.serial_lock.acquire()
            try:
                self.arduino = serial.Serial(self.port, self.baudrate, timeout = self.timeout, write_timeout = self.timeout)
                self.connected = True
            except ValueError:
                self.connected = False
                print("connection failure")
                self.serial_lock.release()
                return False
            self.serial_lock.release()
            return True

    def send_raw_message(self, message):
        if not self.connected:
            raise ConnectionError(self.arduino)

        self.serial_lock.acquire()
        self.written += len(message)
        if self.written > self.write_flush:
            self.arduino.reset_input_buffer()
            self.arduino.reset_output_buffer()
        try:
            if self.arduino.write(message) != len(message):
                self.connected = False
                print("failure sending message")
        except serial.SerialTimeoutException:
            self.connected = False
            print("message time out")
        self.serial_lock.release()

    def send_message(self, cmd, val, rev=False):
        send_val = int(val)
        if send_val < 0 or send_val > 255:
            raise ValueError("val out of range [0,255]")
        checksum = 0b101

        message = bytes([(checksum << 5) | (int(rev) << 4) | cmd, send_val])
        self.send_raw_message(message)

    def send_heartbeat_while_connected(self, interval = 0.2):
        while(self.connected):
            try:
                self.send_message(Command.HEARTBEAT, 0)
            except ConnectionError:
                print("DISCONNECTED: heartbeat failed")
            time.sleep(interval)

    def read_messages(self, interval = 0.05):
        while(self.connected):
            line = self.arduino.readline()
            print(line)

    def start_heartbeat_thread(self, debug=False):
        t = threading.Thread(target=self.send_heartbeat_while_connected)
        t.start()

        if debug:
            t2 = threading.Thread(target=self.read_messages)
            t2.start()

    def set_mode(self, mode):
        self.send_message(Command.MODE, mode)

    def set_steering(self, angle):
        if angle < -1 or angle > 1:
            raise ValueError("angle out of range [-1,1]")
        self.send_message(Command.SET_STEER, int(abs(255 * angle)), rev=(angle < 0))

    def set_throttle(self, throttle):
        if throttle < -1 or throttle > 1:
            raise ValueError("throttle out of range [-1,1]")
        self.send_message(Command.SET_THROTTLE, int(abs(255 * throttle)), rev=(throttle < 0))

    def set_camera(self, angle):
        if angle < -1 or angle > 1:
            raise ValueError("camera angle out of range [-1,1]")
        self.send_message(Command.SET_CAMERA, int(abs(255 * angle)), rev=(angle > 0))

    def set_speed(self, speed):
        if speed < -1 or speed > 1:
            raise ValueError("speed out of range [-1,1]")
        self.send_message(Command.SET_SPEED, int(abs(255 * speed)), rev=(speed < 0))

    def set_distance(self, distance=None, unlimited=False):
        if distance is not None:
            if distance < 0 or distance > 1:
                raise ValueError("distance out of range [0,1]")
            self.send_message(Command.SET_DIST, int(abs(255 * distance)), rev=False)
        elif unlimited:
            self.send_message(Command.SET_DIST, 255, rev=True)

if __name__ == '__main__':
    c = Controller()
    while not c.connected:
        c.connect('/dev/cu.usbmodem141101')
        time.sleep(1)
    print("connected")
    c.start_heartbeat_thread(False)
    print("started heartbeat")

    time.sleep(1)
    c.set_mode(Mode.COMPUTER_SC)

    c.set_steering(1)
    c.set_camera(0)
    c.set_distance(100)
    c.set_speed(5)
