import math
import cv2
import urllib.request
import numpy as np
import netCDF4
import os 

resizeRatio = 1

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

gebco, lats, lons  = open_GEBCO_file('/depthinfo.nc')

def render(lat_deg, lon_deg, zoom = 16):
    global img
    listimg = []
    img = None 
    i = 0
    smurl = r"http://192.168.43.162/hot/{0}/{1}/{2}.png"
    x, y = deg2num(lat_deg, lon_deg, zoom)
    xmin,xmax = x - 1, x + 1
    ymin,ymax = y - 1, y + 1
    lat_deg1, lon_deg1 = num2deg(xmin, ymin, zoom)
    disx, disy = lon_deg - lon_deg1, lat_deg1 - lat_deg

    #print(x,y,xmin,ymin,xmax,ymax)
    for xtile in range(xmin, xmax+1):
        for ytile in range(ymin, ymax+1):
            imgurl=smurl.format(zoom, xtile, ytile)
            print("Opening: " + imgurl)
            try:
                frameResp = urllib.request.urlopen(imgurl)
            except:
                print("Server is not responding")
                quit()
            
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

    #img = cv2.resize(img,(int(img.shape[0]/resizeRatio),int(img.shape[1]/resizeRatio)))
    speed = 1
    cv2.namedWindow("image", cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO)
   #cv2.setWindowProperty("image",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    elevation = -5#get_elevation(lat_deg, lon_deg)
    cv2.rectangle(img,(0,0),(840,30),(0,0,0), cv2.FILLED)
    cv2.line(img,(465,5),(475,15),(0,0,255),3)
    cv2.line(img,(465,15),(475,5),(0,0,255),3)
    cv2.circle(img, (10,130), 10, (153,0,0), -1)
    cv2.circle(img, (10,170), 10, (153,0,0), -1)
    cv2.putText(img,"Speed: "+str(round(speed))+"kmph",(10,20), cv2.FONT_HERSHEY_DUPLEX, .5,(0,255,0),2,cv2.LINE_AA)
    cv2.putText(img,"Satellite: "+str(4),(200,20), cv2.FONT_HERSHEY_DUPLEX, .5,(0,255,0),2,cv2.LINE_AA)
    cv2.putText(img,"Alt/Depth: "+str(elevation),(350,20), cv2.FONT_HERSHEY_DUPLEX, .5,(0,255,0),2,cv2.LINE_AA)
    cv2.imshow("image",img)
    imgfilename = r"img_{0}_{1}_{2}.png"
    cv2.imwrite(imgfilename.format(lat_deg, lon_deg, zoom), img)
    cv2.waitKey()
    cv2.destroyWindow("image")
    

if __name__ == '__main__':
    render(13.762219,121.037923, 16)
