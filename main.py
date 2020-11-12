# coding=utf-8

import cv2

from io import BytesIO
import time
import threading
from flask import Flask, render_template, Response


class VideoCamera(object):
    def __init__(self):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.video = cv2.VideoCapture(0)
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        # self.video = cv2.VideoCapture('video.mp4')
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
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
