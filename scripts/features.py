#!/usr/bin/env python3
import numpy as np
from colorsys import *
import matplotlib as mpl
from scipy.stats import skew
from sklearn import preprocessing
from skimage import filters, color
from PIL import Image, ImageStat, ImageFilter
from skimage.feature import greycomatrix, greycoprops



def colorAvg(im, mask):
    """Takes in a string containing an image file name, returns the average red, blue, and green
        values for all the pixels in that image."""
    imStats = ImageStat.Stat(im, mask)
    print(imStats)
    (redAv, greenAv, blueAv) = imStats.mean
    return redAv, greenAv, blueAv


def colorVariance(im, mask):
    '''Calculates the diversity in color using a hue histogram'''

    # load image pixels
    pix = im.load()
    width, height = im.size
    mask_arr = np.asarray(mask)

    # create empty histogram to be filled with frequencies
    histogram = [0]*360
    pixelHue = 0
    for i in range(width):
        for j in range(height):
            if mask_arr[j,i]:
                (r,g,b) = pix[i,j] #pull out the current r,g,b values
                (h,s,v) = rgb_to_hsv(r/255.,g/255.,b/255.)
                pixelHue = int(360*h)
                #build histogram
                histogram[pixelHue] += 1
    #print histogram
    # calculate standard deviation of histogram
    return np.std(histogram)



def countEdgePixels(im, mask):
    ''' counts the number of pixels that make up the edges of features'''
    # define threshold for edges
    threshold = 150

    # open image and filter
    im2 = im.filter(ImageFilter.FIND_EDGES)
    im2 = im2.convert("L")
    mask_arr = np.asarray(mask)

    # load pixels and count edge pixels
    pix = im2.load()
    pixels = 0
    for x in range(0,im.size[0]):
        for y in range(0, im.size[1]):
            if pix[x,y] > threshold and mask_arr[y,x]:
                pixels += 1

    return float(pixels) / (im.size[0]*im.size[1])

def textureAnalysis(im, mask):
    ''' determines the proportion of the image that has texture'''
    # define texture threshold and grid size
    threshold = 100
    n = 7

    # open image
    width, height = im.size

    # loop across image
    count = 0
    pixList = []
    for i in range(0,width-n,n):
        for j in range(0,height-n,n):

            # divide into small grids
            box = (i,j,i+n,j+n)
            imTemp = im.crop(box)

            # calculate intensity from RGB data
            pixels = list(imTemp.getdata())
            intensity =  [pixels[i][0]+pixels[i][1]+pixels[i][2] for i in range(len(pixels))]

            # count as high texture if difference in intensity is
            # greater than threshold
            if ((max(intensity) - min(intensity)) > threshold):
                count += 1
                pixList += [(i,j)]

    # calculate the percentage of high texture grids

    if width/n == 0: #if width is less than n something is wrong! Check the width and make sure n is a reasonable value.
        print(width)
        raw_input('Oops')
    return float(count)/((width/n)*(height/n))

def yellowFast(im, mask):
    """counts the number of a given color pixels in the given image."""
 #   im = Image.open(imageName)
    #define HSV value ranges for yellow
    #for now just base of Hue - refine for actual yellows seen in field?
    minHue = 20/360.
    maxHue = 150/360.

    minSat = 5/360.
   # maxSat = 0.4

    minV = 190/360.

    width, height = im.size  #find the size of the image
    count = 0 #initialize a counter for yellow pixels.
    rgbList = list(im.getdata())
    maskList = list(mask.getdata())
    hsvList = map(hsv, rgbList)
    for i, (h,s,v) in zip(maskList, hsvList):
        if i and minHue <h and h<maxHue and minSat<s and minV<v:
            count += 1
    totalPix = width*height
    portion = float(count)/totalPix
    return portion

def hsv(colors):
    r,g,b=colors
    return rgb_to_hsv(r/255., g/255., b/255.)

def glcm(im, mask=None, offset=None, features=['contrast', 'dissimilarity', 'homogeneity', 'energy', 'correlation', 'ASM']):
    """Calculate the grey level co-occurrence matrices and output values for
    contrast, dissimilarity, homogeneity, energy, correlation, and ASM in a list"""

    newIm = im
    if not isinstance(im, np.ndarray):
        newIm = np.array(im.convert('L')) #Convert to a grey scale image
    # TODO: check if you want the offset to be a list or just a single value
    if offset is None:
        # we assume the pixel of interest is in the center of the rectangular image
        # and calculate the offset as half of the radius (or 1/4th of the diameter)
        offset = [int(s/4) for s in newIm.shape[::-1]] * 2
    elif type(offset) == int:
        offset = [offset] * 4
    # calculate the glcm and then average over all 4 angles
    # glcm = np.mean(greycomatrix(newIm, offset, [0, np.pi/4, np.pi/2, 3*np.pi/4])[mask], axis=(-1, -2), keepdims=True)
    glcm = np.mean(greycomatrix(newIm, offset, [0, np.pi/4, np.pi/2, 3*np.pi/4]), axis=(-1, -2), keepdims=True)

    returns = []
    for feature in features:
        #Compute all of the grey co occurrence features.
        metric = greycoprops(glcm, feature)[0][0]
        if np.isnan(metric):
            metric = 0
        returns.append([metric])
    return np.concatenate(tuple(returns), 0) #concatenate into one list along axis 0 and return

def colorMoment(im, mask):
    """Calculates the 2nd and 3rd color moments of the input image and returns values in a list."""
    #The first color moment is the mean. This is already considered as a metric for
    #the red, green, and blue channels, so this is not included here.
    #Only the 2nd and 3rd moments will be calculated here.

    newIm = mpl.colors.rgb_to_hsv(im) #convert to HSV space

    #Pull out each channel from the image to analyze seperately.
    HChannel = newIm[:,:,0]
    SChannel = newIm[:,:,1]
    VChannel = newIm[:,:,2]

    #2nd moment = standard deviation.
    Hstd = np.std(HChannel)
    Sstd = np.std(SChannel)
    Vstd = np.std(VChannel)

    #3rd Moment = "Skewness". Calculate the skew, which gives an array.
    #Then take the mean of that array to get a single value for each channel.
    Hskew = np.mean(skew(HChannel))
    Sskew = np.mean(skew(SChannel))
    Vskew = np.mean(skew(VChannel))


    return [Hstd, Sstd, Vstd, Hskew, Sskew, Vskew] #return all of the metrics.


def sameness(im, segments, center=None, radius=None):
    """
        how many of the segments near center are of the same species as it?
        segments can be a mask where pixels are labeled by their class
        or segments can be a list of 2-element tuples: (segments, class_label)
        where "segments" is a list of types: imantics.Polygon.points
    """
    h, w = im.shape[:1]

    # first, get a circular mask around the center
    if center is None: # use the middle of the image
        center = (int(w/2), int(h/2))
    if radius is None: # use the smallest distance between the center and image walls
        radius = min(center[0], center[1], w-center[0], h-center[1])
    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - center[0])**2 + (Y-center[1])**2)
    mask = dist_from_center <= radius

    new_segments = {}
    if type(segments) is list:
        # now, figure out which segments are in the mask
        for i in range(len(segments)):
            # get the centroid of each segment
            centroid = tuple(np.around(segments[i][0].mean(axis=0)).astype(np.uint))[::-1]
            # use the segment only if its centroid is in the mask
            if segments[i][1] not in new_segments:
                new_segments[segments[i][1]] = 0
            if mask[centroid]:
                new_segments[segments[i][1]] += 1
    else:
        # add up all of the pixels in the mask
        for i in np.unique(segments):
            new_segments[i] = np.sum(segments[mask] == i)

    return new_segments
