import cv2
import numpy as np
import glob
 
img_array = []
imgsize = [1,1]

for filename in glob.glob('valid/*.jpg'):
    img = cv2.imread(filename)
    height, width, layers = img.shape
    imgsize = (width,height)
    img_array.append(img)
    
out = cv2.VideoWriter('7117_Caranx_sexfasciatus_juvenile_f.avi',cv2.VideoWriter_fourcc(*'DIVX'), 15, imgsize)
 
for i in range(len(img_array)):
    out.write(img_array[i])
out.release()