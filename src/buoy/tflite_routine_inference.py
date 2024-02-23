from tflite_image_inference import detect_image
import argparse
from glob import glob
import os
import sched, time
import threading
import time
from time import sleep
from threading import Timer
import sx126x
import serial
from datetime import datetime
import pynmea2
import zipfile
import logging 

deviceID = 1
detectionsLastHour = 0
detectionsPerHour = 0
lock = threading.Lock()
node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=868,addr=0,power=22,rssi=True,air_speed=2400,relay=False)
gpsdata = ''
logging.basicConfig(filename='std.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logger=logging.getLogger() 
logger.setLevel(logging.DEBUG) 

class DetectionCounterThread(threading.Thread):
    def __init__(self, numadd):
        self.numadd = numadd
        super(DetectionCounterThread, self).__init__()
    
    def run(self):
        lock.acquire()
        global detectionsLastHour
        detectionsLastHour = detectionsLastHour + self.numadd
        lock.release()
        
    def transfer(self):
        lock.acquire()
        global detectionsPerHour
        global detectionsLastHour
        detectionsPerHour = detectionsLastHour
        lock.release()
        
    def reset(self):
        lock.acquire()
        global detectionsLastHour
        detectionsLastHour = 0
        lock.release()


class ThreadTaskRepeating(object):
  def __init__(self, interval, function, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    self.args = args
    self.kwargs = kwargs
    self.is_running = False
    self.next_call = time.time()
    self.start()

  def _run(self):
    self.is_running = False
    self.start()
    self.function(*self.args, **self.kwargs)

  def start(self):
    if not self.is_running:
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def stop(self):
    self._timer.cancel()
    self.is_running = False
    
def read_gps_data(serial_port='/dev/ttyACM0', baudrate=9600):
    ser = serial.Serial(serial_port, baudrate=baudrate, timeout=1)
    while True:
        data = ser.readline()
        if data.startswith(b'$GPGGA'):
            msg = pynmea2.parse(data.decode('utf-8'))
            message = "Latitude: {param1} | Longitude: {param2}".format(param1 = msg.latitude, param2 = msg.longitude)
            return message


def send_deal(text):
    get_t = text.split(",")

    offset_frequence = int(get_t[1])-(850 if int(get_t[1])>850 else 410)
    #
    # the sending message format
    #
    #         receiving node              receiving node                   receiving node           own high 8bit           own low 8bit                 own 
    #         high 8bit address           low 8bit address                    frequency                address                 address                  frequency             message payload
    data = bytes([int(get_t[0])>>8]) + bytes([int(get_t[0])&0xff]) + bytes([offset_frequence]) + bytes([node.addr>>8]) + bytes([node.addr&0xff]) + bytes([node.offset_freq]) + get_t[2].encode()
    node.send(data)


def add_single_file_to_zip(zip_file_path, file_to_add):
    with zipfile.ZipFile(zip_file_path, 'a') as zip_ref:
        zip_ref.write(file_to_add)

def routine_InitDetect(weights,folder_path,img_size,conf_thres,iou_thres):
    rt = routine_Detect(weights ,folder_path,img_size,conf_thres,iou_thres)

def routine_Detect(weights,folder_path,img_size,conf_thres,iou_thres):
    print("routine_Detect")
    numDetections = 0
    zip_file_path = os.path.join(folder_path,'../zip/images.zip')

    print("Initializing detection Routine...")    
    for file in glob(os.path.join(folder_path,'*')):
        numDetections += detect_image(weights,file,img_size,conf_thres,iou_thres)
        logger.info("Detections for " + file + "is: " + str(numDetections))
        add_single_file_to_zip(zip_file_path, file)
        os.remove(file)

    print("Detected this batch:" + str(numDetections))
    th = DetectionCounterThread(numDetections)
    th.start()
    
def routine_Debug():
    print("detection num" + str(detectionsLastHour))

def routine_HourlyReset():
    th = DetectionCounterThread(0)
    th.transfer()
    th.reset()
    print("new per-hour num" + str(detectionsPerHour))
    
def routine_SendMessage():
    dt = datetime.now()
    lock.acquire()
    global gpsdata
    global detectionsPerHour
    gpsdata = read_gps_data()
    lock.release()
    send_detection = detectionsPerHour
    if detectionsPerHour <= 0:
        send_detection = detectionsLastHour
        
    message = "0,868, Device ID {devid} | Detected: {detect} | Time: {time} | Location: {loc}".format(devid = deviceID, detect = send_detection, time = str(dt), loc = gpsdata)
    send_deal(message)
    logger.info(message)
    print("Lora Message Sent!")


def routine_CaptureImage(folder_path):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    command = "libcamera-still -o " + folder_path + timestr + ".jpg --nopreview --vflip --hflip --width 640 --height 640"
    os.system(command)
   
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-w','--weights', type=str, default='yolov5s-fp16.tflite', help='model.tflite path(s)')
    parser.add_argument('-f','--folder_path', type=str,required=True, help='folder path')  
    parser.add_argument('--img_size', type=int, default=416, help='image size') 
    parser.add_argument('--conf_thres', type=float, default=0.25, help='object confidence threshold')
    parser.add_argument('--iou_thres', type=float, default=0.45, help='IOU threshold for NMS')
    
    opt = parser.parse_args()
    print(opt)

    capture = ThreadTaskRepeating(16, routine_CaptureImage, opt.folder_path)
    detection = ThreadTaskRepeating(60, routine_InitDetect, opt.weights,opt.folder_path,opt.img_size,opt.conf_thres,opt.iou_thres)
    debug = ThreadTaskRepeating(20, routine_Debug)
    reset = ThreadTaskRepeating(3600, routine_HourlyReset)
    send = ThreadTaskRepeating(3, routine_SendMessage)

    while True:
        pass
