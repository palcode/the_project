#!/usr/bin/env python
from __future__ import division
import cv2
import urllib 
import numpy as np
import random


random.seed(12345)

def checkIfValidGlyph(matrix):
    glyph = np.matrix('1 1 1 1 1; 1 0 0 1 1; 1 1 0 0 1; 1 1 0 1 1; 1 1 1 1 1')
    print "Checkin glyph"
    for i in range(4):
        if (matrix==glyph).all():
            return True
        glyph = np.rot90(glyph)

# http://rbrundritt.wordpress.com/2009/10/03/determining-if-two-bounding-boxes-overlap/


# http://opencvpython.blogspot.no/2012/06/sudoku-solver-part-3.html
def rectify(h):
        h = h.reshape((4,2))
        hnew = np.zeros((4,2),dtype = np.float32)
 
        add = h.sum(1)
        hnew[0] = h[np.argmin(add)]
        hnew[2] = h[np.argmax(add)]
         
        diff = np.diff(h,axis = 1)
        hnew[1] = h[np.argmin(diff)]
        hnew[3] = h[np.argmax(diff)]
  
        return hnew

# Implements http://www.aforgenet.com/framework/docs/html/59949f70-2afc-f7a5-1a53-ff99a9208133.htm
# Naive implementation!
def GetEdgePoints(contour):
    edgepoints = []
    
    contour_llhh_sorted_xy = sorted(contour, key= lambda x: (x[0][0], x[0][1]))
    upperleft = contour_llhh_sorted_xy.pop(0)[0]
    lowerright =  contour_llhh_sorted_xy.pop(-1)[0]
    
    contour_llhh_sorted_yx = sorted(contour, key= lambda x: (x[0][1], x[0][0]))
    upperright = contour_llhh_sorted_yx.pop(0)[0]
    lowerleft =  contour_llhh_sorted_yx.pop(-1)[0]
    
    edgepoints.append(upperleft)
    edgepoints.append(lowerright)
    edgepoints.append(upperright)
    edgepoints.append(lowerleft)
    return edgepoints
    
#implements http://www.aforgenet.com/framework/docs/html/e5c7996e-3e9d-ce22-4939-f6ea7c117700.htm
def IsQuadrilateral(four_points): # Assumes convex hull!
    return 0

# Used by sort
def getKey(item):
    return item[0][0]


def glyphFromImage(otsu_roi):
    glyphMatrix = np.matrix('-1 -1 -1 -1 -1;-1 -1 -1 -1 -1;-1 -1 -1 -1 -1;-1 -1 -1 -1 -1;-1 -1 -1 -1 -1')
    height, width = otsu_roi.shape
    #print height, width
    x_roll = int(width/50)
    y_roll = int(height/50)
    for numx in range(0,x_roll):
        for numy in range(0, y_roll):
            #print "Numx",numx, "Numy",numy
            if checkRegionFill(otsu_roi[numx*50:numx*50+50,numy*50:numy*50+50]) > 0.5:
                glyphMatrix[numx, numy] = 1
            else:
                glyphMatrix[numx, numy] = 0
    return glyphMatrix
    
def checkRegionFill(otsu_roi_part):
    height, width = otsu_roi_part.shape
    size = width * height
    fill = size - cv2.countNonZero(otsu_roi_part)
    #print width, height, size, fill
    return (fill/size)
    
    
    
    
    
    
    
    
    
    

cap = cv2.VideoCapture(0)
    
    
stream=urllib.urlopen('http://ptz:ptz@129.241.154.82/mjpg/video.mjpg')
while True:
    ret, source = cap.read()
    sourceClone = source.copy()
    height, width, depth = source.shape
    #print "Image loaded (height, width, depth):", height, width, depth

    gray = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray,(5,5),0) # 5x5 gaussian blur to preprocess before canny
    edges = cv2.Canny(gray, 100, 200) # Canny edge detection with hysteresis 100 to 200

    # Dilate edges
    # kernel = np.ones((5,5),np.uint8)
    #dilation = cv2.dilate(edges,kernel,iterations = 1)

    # Contour detection
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    interestingContoursApprox = []
    interestingContoursROI = []
    minArea = 20.0
    # Use a poly aproximation to identify possible glyph regions, and check for minimum area
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt,0.01*cv2.arcLength(cnt,True),True)
        if len(approx)==4: # Aproximation has four edges, considered square
            area = cv2.contourArea(cnt)
            if area > minArea:
                cv2.drawContours(source,[cnt],0,(0,0,255),4)
                interestingContoursApprox.append(approx)
                #print "ROI Approx",approx
                approx=rectify(approx)
                h = np.array([ [0,0],[249,0],[249,249],[0,249] ],np.float32)
                retval = cv2.getPerspectiveTransform(approx,h)
                warp = cv2.warpPerspective(sourceClone,retval,(250,250))
                interestingContoursROI.append(warp)
                M = cv2.moments(cnt)
                #print "MOMENTS ", M

    interestingContoursOTSU = []
    validGlyhpsFound = []
    for roi in interestingContoursROI:
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        roi_blur = cv2.GaussianBlur(roi_gray,(5,5),0) # 5x5 gaussian blur to preprocess before canny
        # OTSU details http://docs.opencv.org/trunk/doc/py_tutorials/py_imgproc/py_thresholding/py_thresholding.html
        ret, otsu = cv2.threshold(roi_blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        #print "Otsu returned:", ret
        interestingContoursOTSU.append(otsu)
        glyphMatrix = glyphFromImage(otsu)
        if checkIfValidGlyph(glyphMatrix):
            validGlyhpsFound.append(otsu)
    if cv2.waitKey(1) ==27:
        exit(0)
    cv2.imshow('Source',source)

    i = 0
    for valid in validGlyhpsFound:
        i = i + 1
        cv2.imshow(str(i), valid)
