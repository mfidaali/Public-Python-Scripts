import numpy as np
import cv2
import os
from scipy import ndimage

from keras.models import model_from_json, load_model
from keras.utils.generic_utils import CustomObjectScope 
from keras.layers import ReLU, DepthwiseConv2D
from load_model_swish import init_model_swish

model_root = '/home/ubuntu/models/'

# Loads models that need both an .h5 file and .json file
def load_model_with_json(h5, json):
	json_file = open(json, 'r')
	loaded_model_json = json_file.read()
	json_file.close()
	model = model_from_json(loaded_model_json)
	model.load_weights(h5)
	print(h5,'loaded')
	return model

# Crops black borders around the frame
def crop_frame(frame):
    threshVal = 16
	borderThreshRow = 0.5
	borderThreshCol = 0.15
	gray = cv2.cvtColor (frame, cv2.COLOR_BGR2GRAY);
	_,thresh = cv2.threshold(gray, threshVal, 255, cv2.THRESH_BINARY);
	morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), thresh, (-1, -1), 2, cv2.BORDER_CONSTANT, 0);
	tl_y = 0
	tl_x = 0
	br_y = 0
	br_x = 0
	rows, cols = morph.shape
	for i in range(rows):
		#print(str(i) + ' '+str(cv2.countNonZero(morph[i, 0:rows])) + '   ' + str(borderThresh * cols))
		if cv2.countNonZero(morph[i, 0:rows]) > (borderThreshCol * cols):
			tl_y = i
			break
	for i in range(cols):
		#print(str(i) + ' '+str(cv2.countNonZero(morph[0:cols, i])) + '   ' + str(borderThresh * rows))
		if cv2.countNonZero(morph[0:cols, i]) > (borderThreshRow * rows):
			tl_x = i
			break
	for i in reversed(range(rows)):
		if cv2.countNonZero(morph[i, 0:rows]) > (borderThreshCol * cols):
			br_y = i
			break
	for i in reversed(range(cols)):
		if cv2.countNonZero(morph[0:cols, i]) > (borderThreshRow * rows):
			br_x = i
			break
	crop_img = frame[tl_y:br_y, tl_x:br_x]
	return crop_img, tl_x, tl_y 

# Resizes the frame to specified size sz
def resize_frame(frame, sz):
    img = cv2.resize(frame, (sz, sz))
	img = img / 255.
	img = img[:,:,::-1]
	img = np.expand_dims(img, 0)
	return img

def load_AI1():
	with CustomObjectScope({'relu6': ReLU(6.),'DepthwiseConv2D': DepthwiseConv2D}):
		model_AI1 = load_model(model_root+"AI1/binaryClassifier.h5")
		model_AI1_multi = load_model(model_root+"AI1/multi/multiClassifier.h5")

	return (model_AI1, model_AI1_multi)

def load_yoloAI():
	model_yolo = load_model_with_json(model_root+'yolo/AI.hdf5',model_root+'yolo/yolo_detector.json')

	return model_yolo

def secs_to_timestring(secs):
	hour = int(secs / 60 / 60)
	minute = int((secs / 60) % 60)
	second = secs % 60

	s = ""

	if hour < 10:
		s += "0"
	s += str(hour)+":"

	if minute < 10:
		s += "0"
	s += str(minute)+":"

	if second < 10:
		s += "0"
	s += str(second)

	return s

def timestring_to_secs(timestring):
	units = timestring.split(':')
	hour = int(units[0]) * 60 * 60
	minute = int(units[1]) * 60
	second = int(units[2])

	return hour + minute + second

#Function for uploading to S3
def uploadToS3(cmd, src, dest):
    print("\nStarting to "+ cmd + " data to S3")
    s3_cmd = 'aws s3 ' + cmd +' '+ src +' '+dest 
    try:
        os.system(s3_cmd)
    except:
        print("Upload to S3 Failed")

