# USAGE
# python object_tracker.py --prototxt deploy.prototxt --model res10_300x300_ssd_iter_140000.caffemodel

# import the necessary packages
from pyimagesearch.centroidtracker import CentroidTracker
from imutils.video import VideoStream
import numpy as np
import argparse
import imutils
import time
import cv2
import scipy
import requests


def opera_luz(estado):
    url = "http://192.168.100.100/ifttt.php?evento="
    if estado == 1:
        comando = url + "porton_on"
        print("Encendiendo")
    else:
        comando = url + "porton_off"
        print ("Apagando")
    print(comando)
    requests.get(comando)


# http://192.168.100.100/ifttt.php?evento=porton_on


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--prototxt", required=True,
                help="path to Caffe 'deploy' prototxt file")
ap.add_argument("-m", "--model", required=True,
                help="path to Caffe pre-trained model")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
                help="minimum probability to filter weak detections")
args = vars(ap.parse_args())
estadoAnterior = 1
# initialize our centroid tracker and frame dimensions
ct = CentroidTracker()
(H, W) = (None, None)

# load our serialized model from disk
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])

# initialize the video stream and allow the camera sensor to warmup
print("[INFO] starting video stream...")
# vs = VideoStream(src=0).start()
vs = VideoStream(src="http://192.168.100.50:8081").start()
time.sleep(2.0)
primeroListaAnterior = -1
presenteframes = 0
# loop over the frames from the video stream
while True:
    # read the next frame from the video stream and resize it
    frame = vs.read()
    frame = imutils.resize(frame, width=400)
    time.sleep(.8)
    # if the frame dimensions are None, grab them
    if W is None or H is None:
        (H, W) = frame.shape[:2]

    # construct a blob from the frame, pass it through the network,
    # obtain our output predictions, and initialize the list of
    # bounding box rectangles
    blob = cv2.dnn.blobFromImage(frame, 1.0, (W, H),
                                 (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()
    rects = []

    # loop over the detections
    for i in range(0, detections.shape[2]):
        # filter out weak detections by ensuring the predicted
        # probability is greater than a minimum threshold
        if detections[0, 0, i, 2] > args["confidence"]:
            # compute the (x, y)-coordinates of the bounding box for
            # the object, then update the bounding box rectangles list
            box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
            rects.append(box.astype("int"))

            # draw a bounding box surrounding the object so we can
            # visualize it
            (startX, startY, endX, endY) = box.astype("int")
    #			cv2.rectangle(frame, (startX, startY), (endX, endY),
    #				(0, 255, 0), 2)

    # update our centroid tracker using the computed set of bounding
    # box rectangles
    objects = ct.update(rects)
    if len(objects) > 0:
        primeroLista = list(objects.keys())[0]
    else:
        primeroLista = -1
    if primeroListaAnterior != primeroLista:
        primeroListaAnterior = primeroLista
        presenteframes = 0
    else:
        presenteframes += 1

    # loop over the tracked objects
    for (objectID, centroid) in objects.items():
        # draw both the ID of the object and the centroid of the
        # object on the output frame
        text = "ID {}".format(objectID)
    #		cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
    #			cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    #		cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)
    #	text = "Primero Lista " + str(primeroLista)
    text = "Hay alguien en la puerta "
    if primeroLista > -1 and presenteframes > 2:
        cv2.putText(frame, text, (10, 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        print("Cara detectada")
        if estadoAnterior == 0:
            opera_luz(1)
        estadoAnterior = 1
    if presenteframes > 20 and primeroLista == -1:
        if estadoAnterior == 1:
            opera_luz(0)
        estadoAnterior = 0

    # show the output frame
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
