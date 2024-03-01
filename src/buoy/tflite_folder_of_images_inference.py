from tflite_image_inference import detect_image
import argparse
from glob import glob
import os
import cv2
from PIL import Image, ImageOps
import time
from utils import letterbox_image, scale_coords
import numpy as np


def detect_from_folder_of_images(weights,folder_path,img_size,conf_thres,iou_thres):

    for file in glob(os.path.join(folder_path,'*')):
        print('Processing ',file,' now ...')
        
        result_boxes, result_scores, result_class_names, img, original_size = detect_image(weights,file,img_size,conf_thres,iou_thres)
        size = (img_size,img_size)

        if len(result_boxes) > 0:
            result_boxes = scale_coords(size,np.array(result_boxes),(original_size[1],original_size[0]))
            font = cv2.FONT_HERSHEY_SIMPLEX 

            # org 
            org = (20, 40) 

            # fontScale 
            fontScale = 0.5

            # Blue color in BGR 
            color = (0, 255, 0) 

            # Line thickness of 1 px 
            thickness = 1

            for i,r in enumerate(result_boxes):
                org = (int(r[0]),int(r[1]))
                cv2.rectangle(img, (int(r[0]),int(r[1])), (int(r[2]),int(r[3])), (255,0,0), 1)
                cv2.putText(img, str(int(100*result_scores[i])) + '%  ' + str(result_class_names[i]), org, font,  
                            fontScale, color, thickness, cv2.LINE_AA)

        save_result_filepath = file.split('/')[-1].split('results')[0] + 'yolov5_output.jpg'
        cv2.imwrite(save_result_filepath,img[:,:,::-1])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-w','--weights', type=str, default='yolov5s-fp16.tflite', help='model.tflite path(s)')
    parser.add_argument('-f','--folder_path', type=str,required=True, help='folder path')  
    parser.add_argument('--img_size', type=int, default=416, help='image size') 
    parser.add_argument('--conf_thres', type=float, default=0.25, help='object confidence threshold')
    parser.add_argument('--iou_thres', type=float, default=0.45, help='IOU threshold for NMS')

    
    opt = parser.parse_args()
    
    print(opt)
    detect_from_folder_of_images(opt.weights,opt.folder_path,opt.img_size,opt.conf_thres,opt.iou_thres)
