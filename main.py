# coding=utf-8

import cv2

import time
import threading
from flask import Flask, render_template, Response


class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        while True:
            if success:
                break
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

outputFrame = None
condition = threading.Condition()
loginfo = 'running'

app = Flask(__name__)

@app.route('/')
def index():
    global loginfo
    """Video streaming home page."""
    return render_template('index.html', loginfo = loginfo)


def get_frame(cam):
    global outputFrame
    while True:
        try:
            success, image = cam.video.read()
            ret, jpeg = cv2.imencode('.jpg', image)
            #with lock:
            with condition:
                outputFrame = jpeg.tobytes()
                condition.notify_all()



        except Exception as e:
            loginfo = 'error, %s. \r\n\r\n Try again in %s seconds.' % (e, str(2))
            print(loginfo)
            time.sleep(2)
            pass


def generate():
    """Video streaming generator function."""

    global outputFrame

    while True:
        with condition:
            condition.wait()
            # if outputFrame is None:
            #     continue
            encodedImage = outputFrame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n'
               b'Content-Length: '+ bytes(str(len(encodedImage)),encoding='utf-8') + b'\r\n'
               b'\r\n' +
               encodedImage + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":


    print("Open camera...")
    local_cam = VideoCamera()
    print("start streaming...")
    t1 = threading.Thread(target=get_frame,args=(local_cam,))
    t1.daemon = True
    t1.start()
    app.run(host='0.0.0.0', threaded=True, debug=True, port="8080", use_reloader=False)
