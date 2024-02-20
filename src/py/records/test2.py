import numpy as np
import netCDF4
#import serial
import time
import string 
import pynmea2
import datetime

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
    NetCDF_dataset = netCDF4.Dataset(filepath)
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


port="/dev/ttyAMA0"
#ser=serial.Serial(port,baudrate=9600,timeout=0.5)
#dataout =pynmea2.NMEAStreamReader()
#newdata=ser.readline()
#print(newdata)
gebco, lats, lons  = open_GEBCO_file('depthinfo.nc')
now = datetime.datetime.now()
lat = 13.9155403598569
lng = 120.819197351031
dep=get_elevation(lat,lng)
gps= str(now) + " Latitude: " +str(lat)+ " Longitutde: " +str(lng) + " Depth:" + str(dep)
print(gps) 
#record.write(gps + '\n' ) 

