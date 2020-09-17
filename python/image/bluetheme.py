#!/usr/bin/env python

import glob
import cv2 as cv

files = glob.glob("*.jpg")
for f in files:
	image = cv.imread(f)
	height = image.shape[0]
	width = image.shape[1]
	cv.line(image, (0, 0), (width, height), (255, 0, 0), 10)
	cv.imwrite("blue/" + f, image)
