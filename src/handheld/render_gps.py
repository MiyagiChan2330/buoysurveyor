import cv2
import time
import math
import serial
import pynmea2
import urllib.request
import numpy as np
import netCDF4
import sx126x
import os 

zoom = 16
request = False

def geo_idx(dd, dd_array):
    #
    #   returns the index of the closest degrees decimal value in the array.
    #   dd = degrees decimal (Float64)
    #   dd_array = arrach of degrees decimal values (Float64)
    #
    #
    geo_index = (np.abs(dd_array - dd)).argmin()
    return geo_index

def open_GEBCO_file(filepath):
    #
    #   returns dataset in NetCDF format and from the dataset arrays of the latitudes and longitudes
    #   filepath = filepath to GEBCO file
    #
    #
    dir_path = os.path.dirname(os.path.realpath(__file__)) + filepath
    NetCDF_dataset = netCDF4.Dataset(dir_path)
    lats = NetCDF_dataset.variables['lat'][:]
    lons = NetCDF_dataset.variables['lon'][:]
    return NetCDF_dataset, lats, lons

def get_GEBCO_info(dataset):
    #
    #   prints metadata in GEBCO file
    #
    #
    print(dataset.data_model)

    for attr in dataset.ncattrs():
        print(attr, '=', getattr(dataset, attr))

    print(dataset.variables)
    return

def get_elevation(lat, lon):
    #
    # returns the elevation given a latitude and longitude
    #
    lat_index = geo_idx(lat, lats)
    lon_index = geo_idx(lon, lons)
    return gebco.variables['elevation'][lat_index, lon_index]

def ecv(event, x, y, flags, param):
    global zoom
    if event == cv2.EVENT_LBUTTONDOWN:
        if (x in range(465,480) and y in range(0,20)):
            cv2.destroyWindow(winname)
            exit()
        elif (x in range(0,20) and y in range(120,140)):
             zoom = min(zoom + 1, 16)
        elif (x in range(0,20) and y in range(160,180)):
             zoom = max(zoom - 1, 14)

def get_slope(lat, lon):
    elevpoint = get_elevation(lat, lon)
    elevwest = get_elevation(lat, lon - 0.005)
    eleveast = get_elevation(lat, lon + 0.005)
    elevnorth = get_elevation(lat - 0.0005, lon)
    elevsouth = get_elevation(lat + 0.0005, lon)

    elevsidetotal = elevwest + eleveast + elevnorth + elevsouth
    elevsidetotal /= 4

    return abs(elevsidetotal - elevpoint)

winname = "render"
cv2.namedWindow(winname, cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO)
cv2.setWindowProperty(winname,cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
cv2.moveWindow(winname, 0,0)
cv2.setMouseCallback(winname, ecv)
oldtime = 0
baud = 9600
p = '/dev/ttyACM0'
ser = serial.Serial(port=p, baudrate=baud)
time.sleep(2)
#
#
#Sea floor height (above mean sea level)
#
#
#Tests
#
gebco, lats, lons  = open_GEBCO_file('/depthinfo.nc')
node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=868,addr=0,power=22,rssi=True,air_speed=2400,relay=False)

def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)

def rendersphere(lat_deg, lon_deg, img, red,green,blue, text, text2, zoom = 16):
    x, y = deg2num(lat_deg, lon_deg, zoom)
    xmin,xmax = x - 1, x + 1
    ymin,ymax = y - 1, y + 1
    lat_deg1, lon_deg1 = num2deg(xmin, ymin, zoom)
    disx, disy = lon_deg - lon_deg1, lat_deg1 - lat_deg
    pix = round(disx*256/(num2deg(xmin,ymin,zoom)[0] - num2deg(xmin,ymin+1,zoom)[0]))
    piy = round(disy*256/(num2deg(xmin+1,ymin,zoom)[1] - num2deg(xmin,ymin,zoom)[1]))

    cv2.circle(img,(pix,piy), 7, (255,255,255), -1)
    cv2.circle(img,(pix,piy), 5, (red,green,blue), -1)
    cv2.putText(img, text ,(pix + 20 ,piy), cv2.FONT_HERSHEY_COMPLEX_SMALL, .5,(0,0,0),1,cv2.LINE_AA)
    cv2.putText(img, text2 ,(pix + 20 ,piy + 20), cv2.FONT_HERSHEY_COMPLEX_SMALL, .5,(0,0,0),1,cv2.LINE_AA)

    return img

def centerimage(lat_deg, lon_deg, img, zoom = 16):
    x, y = deg2num(lat_deg, lon_deg, zoom)
    xmin,xmax = x - 1, x + 1
    ymin,ymax = y - 1, y + 1
    lat_deg1, lon_deg1 = num2deg(xmin, ymin, zoom)
    disx, disy = lon_deg - lon_deg1, lat_deg1 - lat_deg
    pix = round(disx*256/(num2deg(xmin,ymin,zoom)[0] - num2deg(xmin,ymin+1,zoom)[0]))
    piy = round(disy*256/(num2deg(xmin+1,ymin,zoom)[1] - num2deg(xmin,ymin,zoom)[1]))
    img = img[piy-145:piy+145, pix-240:pix+240]
    return img

def render(lat_deg, lon_deg, zoom = 16):
    listimg = []
    img = None 
    i = 0
    smurl = r"http://localhost/hot/{0}/{1}/{2}.png"
    x, y = deg2num(lat_deg, lon_deg, zoom)
    xmin,xmax = x - 1, x + 1
    ymin,ymax = y - 1, y + 1

    for xtile in range(xmin, xmax+1):
        for ytile in range(ymin, ymax+1):
            imgurl=smurl.format(zoom, xtile, ytile)
            try:
                frameResp = urllib.request.urlopen(imgurl)
            except:
                print("Server is not responding")
                pass
            
            frameNp = np.array(bytearray(frameResp.read()),dtype=np.uint8)
            if img is None:
                img = cv2.imdecode(frameNp,-1)
            else:
                img1 = cv2.imdecode(frameNp,-1)
                img = np.concatenate((img, img1), axis=0)
        listimg.append(img)
        i += 1
        img = None
    for x in range(0,i):
        if img is None:
            img = listimg[x]
        else:
            img1 = listimg[x]
            img = np.concatenate((img, img1), axis=1)
            
    return img
 
if ser.is_open:
    while True:
        size = ser.inWaiting()
        if size:
            if time.time() - oldtime > 2 or request == True:
                request = False
                oldtime = time.time()
                data = str(ser.read(size))
                data = data[2:len(data)-1]
                predata = data.split('\\r\\n')
            #print(data)
            #print(predata)
            try:
                data = pynmea2.parse(predata[[i for i, s in enumerate(predata) if '$GPGGA' in s][0]])
                dataspeed = pynmea2.parse(predata[[i for i, s in enumerate(predata) if '$GPVTG' in s][0]])
                speed = dataspeed.spd_over_grnd_kmph
                if (data.latitude == 0.0 or data.longitude == 0.0): request = True
                #print(data.latitude,data.longitude)
                frame = render(data.latitude,data.longitude,zoom)
                node.receive()
                elevation = get_elevation(data.latitude, data.longitude)
                slope = get_slope(data.latitude, data.longitude)

                cv2.rectangle(frame,(0,0),(480,30),(0,0,0), cv2.FILLED)
                cv2.line(frame,(465,5),(475,15),(0,0,255),3)
                cv2.line(frame,(465,15),(475,5),(0,0,255),3)

                frame = rendersphere(data.latitude, data.longitude, frame, 0,255,0, "", "", zoom)

                cv2.putText(frame,"Speed: "+str(round(speed))+"kmph",(5,20), cv2.FONT_HERSHEY_SIMPLEX, .45,(0,255,0),1,cv2.LINE_AA)
                cv2.putText(frame,"Satellite: "+str(4),(125,20), cv2.FONT_HERSHEY_SIMPLEX, .45,(0,255,0),1,cv2.LINE_AA)
                cv2.putText(frame,"Alt/Depth: "+str(elevation) +"m",(225,20), cv2.FONT_HERSHEY_SIMPLEX, .45,(0,255,0),1,cv2.LINE_AA)
                cv2.putText(frame,"Slope: "+str(slope),(350,20), cv2.FONT_HERSHEY_SIMPLEX, .45,(0,255,0),1,cv2.LINE_AA)
                cv2.imshow(winname, frame)
                txt = "image_{lat:.3f}_{lon:.3f}"
                cv2.imwrite(txt.format(lat = data.latitude, lon = data.longitude),frame)
                cv2.waitKey(10)
            #except Exception as e: print(e)
            except: pass
        #time.sleep(.3)
