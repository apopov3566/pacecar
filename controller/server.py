import controller
from flask import Flask
from flask import render_template, Response
import time
import cv2

app = Flask(__name__)

c = controller.Controller()
c.connect()
camera = cv2.VideoCapture(0)

time.sleep(1)
c.set_mode(controller.Mode.COMPUTER)

@app.route('/')
def json():
    return render_template('json.html')

@app.route('/w')
def w():
    c.set_throttle(0.2)
    return ("nothing")

@app.route('/s')
def s():
    c.set_throttle(-0.2)
    return ("nothing")

@app.route('/a')
def a():
    c.set_steering(-0.5)
    return ("nothing")

@app.route('/d')
def d():
    c.set_steering(0.5)
    return ("nothing")

@app.route('/cs')
def cs():
    c.set_steering(0)
    return ("nothing")

@app.route('/ct')
def ct():
    c.set_throttle(0)
    return ("nothing")

@app.route('/smc')
def smc():
    c.set_mode(controller.Mode.COMPUTER)
    return ("nothing")

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames():  
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

if __name__ == "__main__":
    app.run(host='0.0.0.0')