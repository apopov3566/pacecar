import controller
import camera
import questioner
from flask import Flask, render_template, Response, request
import time
import threading

app = Flask(__name__)

c = controller.Controller()
cam = camera.Camera()
q = questioner.Questioner(c, cam)
q.run("ODQzNTA1MTA3MDE4MTg2NzUy.YKE1WQ.HR36xuZi_w8o3FSP6kjaK1oDqsc")
c.connect('/dev/cu.usbmodem141101')
time.sleep(1)
c.set_mode(controller.Mode.COMPUTER)

@app.route('/car_control')
def car_control():
    cam.run()
    return render_template('car_control.html', stop_img = "static/stop.png", go_img = "static/go.png")

@app.route('/camera_control')
def camera_control():
    cam.run()
    return render_template('camera_control.html')

@app.route('/rando')
def admin_console():
    cam.run()
    return render_template('admin_console.html')


@app.route('/set_steer')
def set_steer():
    # c.set_mode(controller.Mode.COMPUTER)
    c.set_steering(int(request.args.get("steer"))/100)
    return ("nothing")

@app.route('/set_throttle')
def set_throttle():
    # c.set_mode(controller.Mode.COMPUTER)
    c.set_throttle(int(request.args.get("throttle"))/100*0.3)
    return ("nothing")

@app.route('/set_camera')
def set_camera():
    # c.set_mode(controller.Mode.COMPUTER)
    c.set_camera(int(request.args.get("camera"))/100)
    return ("nothing")

@app.route('/set_x')
def set_x():
    cam.set_x(int(request.args.get("x"))/100)
    return ("nothing")

@app.route('/set_y')
def set_y():
    cam.set_y(int(request.args.get("y"))/100)
    return ("nothing")

@app.route('/set_car_mode')
def set_car_mode():
    c.set_mode(int(request.args.get("mode")))
    return ("nothing")

@app.route('/set_camera_mode')
def set_camera_mode():
    cam.set_mode(int(request.args.get("mode")))
    return ("nothing")

@app.route('/set_questioner_done')
def set_questioner_done():
    cam.scanned.value = True
    return ("nothing")

@app.route('/set_size')
def set_size():
    cam.set_size(int(request.args.get("size"))/100)
    return ("nothing")

@app.route('/set_command')
def set_command():
    command_speed = 0.5
    print(request.args.get("steer"), request.args.get("distance"))
    if int(request.args.get("distance")) < 0:
        c.set_mode(controller.Mode.COMPUTER)
        c.set_throttle(0)
        time.sleep(0.05)
        c.set_throttle(-0.3)
        time.sleep(0.05)
        c.set_throttle(0)
        time.sleep(0.05)
    c.set_mode(controller.Mode.COMPUTER_SC)
    c.set_steering(int(request.args.get("steer"))/100)
    c.set_speed(command_speed if int(request.args.get("distance")) >= 0 else -command_speed)
    c.set_distance(abs(int(request.args.get("distance"))/100))
    return ("nothing")

@app.route('/do_reverse')
def do_reverse():
    # c.set_mode(controller.Mode.COMPUTER)
    c.set_throttle(0)
    time.sleep(0.05)
    c.set_throttle(-0.3)
    time.sleep(0.05)
    c.set_throttle(0)
    return ("nothing")

@app.route('/do_scan')
def do_scan():
    cam.scan()
    return ("nothing")

@app.route('/check_password')
def check_password():
    if request.args.get("password") == cam.password:
        #cam.start_password_timer()
        return ("{\"status\" : \"valid\"}")
    else:
        return ("{\"status\" : \"invalid\"}")


@app.route('/set_password')
def set_password():
    cam.password = request.args.get("password")
    return ("nothing")

@app.route('/set_round')
def set_round():
    if request.args.get("round") in ["1","2","3","4"]:
        q.set_round(int(request.args.get("round")) - 1)
    return ("nothing")

if __name__ == "__main__":
    app.run(host='0.0.0.0')
