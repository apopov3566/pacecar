import cv2
import multiprocessing
import threading
from enum import IntEnum
from PIL import Image
import zbarlight
import numpy as np
import time

class CameraMode(IntEnum):
    BLANK = 0
    NORMAL = 1
    EXIT = 2

class CameraCommand(IntEnum):
    X = 0
    Y = 1
    SIZE = 2
    SCAN = 3
    MODE = 4
    COUNTDOWN = 5

class Camera:
    def __init__(self) -> None:
        self.running = False
        self.p = None

        self.max_size = 1 # max prop of height
        self.password = "test_pw"
        self.root_password = "admin_control"

        self.scanned = multiprocessing.Value('i', False)

        self.queue = multiprocessing.Queue()

    def password_timer(self, next_password, sleep_time):
        time.sleep(sleep_time)
        self.password = next_password

    def start_password_timer(self,next_password):
        th = threading.Thread(target=self.password_timer,args=(next_password,120,))
        th.start()

    def stream_frames(self, queue):
        cap = cv2.VideoCapture(0)

        x=0
        y=0
        size=1
        scan = False
        mode = CameraMode.BLANK
        countdown = -1
        countdown_start = -1

        while(True):
            # Capture frame-by-frame
            try:
                while(True):
                    c, v = self.queue.get(False)
                    
                    if c == CameraCommand.X:
                        x = v
                    elif c == CameraCommand.Y:
                        y = v
                    elif c == CameraCommand.SIZE:
                        size = v
                    elif c == CameraCommand.SCAN:
                        scan = True
                    elif c == CameraCommand.MODE:
                        mode = v
                    elif c == CameraCommand.COUNTDOWN:
                        if v >= 0:
                            countdown = v
                            countdown_start = time.time()
                        else:
                            countdown = -1
                            countdown_start = -1
            except:
                pass

            ret, frame = cap.read()
            height, width, channels = frame.shape

            if mode == CameraMode.NORMAL:
                rect_center_x = int(width/2 + width/2 * x)
                rect_center_y = int(height/2 + height/2 * y)
                rect_size = int(size * self.max_size * height/2)
                rect_start = (rect_center_x - rect_size, rect_center_y - rect_size)
                rect_end = (rect_center_x + rect_size, rect_center_y + rect_size)
                #print(rect_start, rect_end)
                color =  (0, 0, 255) if scan else (0, 255, 0)
                frame = cv2.rectangle(frame, rect_start, rect_end, color, 3)

                frame = cv2.line(frame, (rect_center_x, 0), (rect_center_x, rect_center_y - rect_size), color, 1)
                frame = cv2.line(frame, (rect_center_x, height), (rect_center_x, rect_center_y + rect_size), color, 1)
                frame = cv2.line(frame, (0, rect_center_y), (rect_center_x - rect_size, rect_center_y), color, 1)
                frame = cv2.line(frame, (width, rect_center_y), (rect_center_x + rect_size, rect_center_y), color, 1)

                if countdown != -1:
                    frame = cv2.putText(frame, "Time left: " + str(int(max(countdown + countdown_start - time.time(), 0))) + "s", (1550,1050), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,0), 2, cv2.LINE_AA)

                if scan:
                    print("SCAN!")
                    crop = frame[max(rect_center_y - rect_size, 0):min(rect_center_y + rect_size, 1079), max(rect_center_x - rect_size, 0): min(rect_center_x + rect_size, 1919)]
                    #cv2.imshow('crop', crop)
                    img = Image.fromarray(crop)
                    codes = zbarlight.scan_codes(['qrcode'], img)
                    print('QR codes: %s' % codes)
                    if codes is not None and len(list(filter(lambda x: x.decode("utf-8") in ["nova", "ravager"], codes))) > 0:
                         print("CODE FOUND")
                         self.queue.put((CameraCommand.MODE, CameraMode.EXIT), True)
                         self.scanned.value = True
                    scan = False
            elif mode == CameraMode.EXIT:
                frame = np.zeros((height,width,channels))
                frame = cv2.putText(frame, 'CODE FOUND', (470,500), cv2.FONT_HERSHEY_SIMPLEX, 5, (0,0,255), 10, cv2.LINE_AA)
                frame = cv2.putText(frame, '[consult team leader for decoding]', (440,600), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 3, cv2.LINE_AA)
            else:
                frame = np.zeros((height,width,channels))
                frame = cv2.putText(frame, '[connecting]', (750,550), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 4, cv2.LINE_AA)

            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()

    def run(self):
        if not self.running:
            self.running = True
            self.p = multiprocessing.Process(target=self.stream_frames, args=(self.queue,))
            self.p.start()

    def set_x(self, v):
        self.queue.put((CameraCommand.X, v))

    def set_y(self, v):
        self.queue.put((CameraCommand.Y, v))

    def set_size(self, v):
        self.queue.put((CameraCommand.SIZE, v))

    def scan(self):
        self.queue.put((CameraCommand.SCAN, None))

    def set_mode(self, mode):
        self.queue.put((CameraCommand.MODE, mode))

    def set_countdown(self, v):
        self.queue.put((CameraCommand.COUNTDOWN, v))