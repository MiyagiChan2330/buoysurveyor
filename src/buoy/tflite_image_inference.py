from tflite_inference import yolov5_tflite
import argparse
import cv2
import time
from PIL import Image, ImageOps
import numpy as np
from utils import letterbox_image, scale_coords
import sys
import threading
import time
import select
import termios
import tty
import serial
from datetime import datetime
from threading import Timer


def detect_image(weights,image_url,img_size,conf_thres,iou_thres):

    start_time = time.time()
    
    #image = cv2.imread(image_url)
    image = Image.open(image_url)
    original_size = image.size[:2]
    size = (img_size,img_size)
    image_resized = letterbox_image(image,size)
    img = np.asarray(image)
    
    #image = ImageOps.fit(image, size, Image.ANTIALIAS)
    image_array = np.asarray(image_resized)

    normalized_image_array = image_array.astype(np.float32) / 255.0

    yolov5_tflite_obj = yolov5_tflite(weights,img_size,conf_thres,iou_thres)

    result_boxes, result_scores, result_class_names = yolov5_tflite_obj.detect(normalized_image_array)
    end_time = time.time()
    print('FPS:',1/(end_time-start_time))
    print('Imgname:',image_url)
    print('Detections:',len(result_boxes))

    return result_boxes, result_scores, result_class_names, img, original_size



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-w','--weights', type=str, default='yolov5s-fp16.tflite', help='model.tflite path(s)')
    parser.add_argument('-i','--img_path', type=str, required=True, help='image path')  
    parser.add_argument('--img_size', type=int, default=416, help='image size')  
    parser.add_argument('--conf_thres', type=float, default=0.25, help='object confidence threshold')
    parser.add_argument('--iou_thres', type=float, default=0.45, help='IOU threshold for NMS')

    
    opt = parser.parse_args()
    
    print(opt)
    detect_image(opt.weights,opt.img_path,opt.img_size,opt.conf_thres,opt.iou_thres)


    
