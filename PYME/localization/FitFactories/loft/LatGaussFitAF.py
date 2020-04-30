#!/usr/bin/python

##################
# LatGaussFitAF.py
#
# Copyright David Baddeley, 2009
# d.baddeley@auckland.ac.nz
#
# This file may NOT be distributed without express permision from David Baddeley
#
##################

import scipy
from scipy.signal import interpolate
import scipy.ndimage as ndimage
from pylab import *
# try:
#     # noinspection PyCompatibility
#     import copy_reg
# except ImportError:
#     #py3
#     import copyreg as copy_reg
# import numpy

from gauss_app import *

from scipy import weave

from _fithelpers import *

# def pickleSlice(slice):
#         return unpickleSlice, (slice.start, slice.stop, slice.step)
#
# def unpickleSlice(start, stop, step):
#         return slice(start, stop, step)
#
# copy_reg.pickle(slice, pickleSlice, unpickleSlice)

def f_gauss2dA(p, X, Y):
    """2D Gaussian model function with linear background - parameter vector [A, x0, y0, sigma, background, lin_x, lin_y]"""
    A, x0, y0, sx, sy, b, b_x, b_y = p
    #return A*scipy.exp(-((X-x0)**2 + (Y - y0)**2)/(2*s**2)) + b + b_x*X + b_y*Y
    r = genGaussA(X,Y,A,x0,y0,sx, sy,b,b_x,b_y)
    r.strides = r.strides #Really dodgy hack to get around something which numpy is not doing right ....
    return r

def f_gauss2dAF(p, X, Y):
    """2D Gaussian model function with linear background - parameter vector [A, x0, y0, sigma, background, lin_x, lin_y] - uses fast exponential approx"""
    A, x0, y0, sx, sy, b, b_x, b_y = p
    #return A*scipy.exp(-((X-x0)**2 + (Y - y0)**2)/(2*s**2)) + b + b_x*X + b_y*Y
    r = genGaussAF(X,Y,A,x0,y0,sx, sy,b,b_x,b_y)
    r.strides = r.strides #Really dodgy hack to get around something which numpy is not doing right ....
    return r


class GaussianFitResult:
    def __init__(self, fitResults, metadata, slicesUsed=None, resultCode=None, fitErr=None):
        self.fitResults = fitResults
        self.metadata = metadata
        self.slicesUsed = slicesUsed
        self.resultCode=resultCode
        self.fitErr = fitErr
    
    def A(self):
        return self.fitResults[0]

    def x0(self):
        return self.fitResults[1]

    def y0(self):
        return self.fitResults[2]

    def sigma(self):
        return self.fitResults[3]

    def background(self):
        return self.fitResults[4]

    def FWHMnm(self):
        return FWHM_CONV_FACTOR*self.fitResults[3]*self.metadata.voxelsize_nm*x

    def correctedFWHM(self, FWHM_PSF):
        return scipy.sqrt(self.FWHMnm()**2 - self.FWHM_PSF**2)

    def renderFit(self):
        vs = self.metadata.voxelsize_nm
        X = vs.x*scipy.mgrid[self.slicesUsed[0]]
        Y = vs.y*scipy.mgrid[self.slicesUsed[1]]
        return f_gauss2d(self.fitResults, X, Y)
        


class GaussianFitFactory:
    def __init__(self, data, metadata, fitfcn=f_gauss2dAF):
        """Create a fit factory which will operate on image data (data), potentially using voxel sizes etc contained in
        metadata. """
        self.data = data
        self.metadata = metadata
        self.fitfcn = fitfcn #allow model function to be specified (to facilitate changing between accurate and fast exponential approwimations)
        #self.ccdReadNoise = ccdReadNoise #readout noise in electrons
        #self.noiseFactor = noiseFactor #EM noise factor
        #self.electronsPerCount = electronsPerCount

    def __getitem__(self, key):
        #print key
        xslice, yslice, zslice = key

        #cut region out of data stack
        dataROI = self.data[xslice, yslice, zslice]

        #average in z
        dataMean = dataROI.mean(2)

        #generate grid to evaluate function on
        #X,Y = scipy.mgrid[xslice, yslice]
        #X = scipy.mgrid[xslice]
        #Y = scipy.mgrid[yslice]
        vs = self.metadata.voxelsize_nm
        X = vs.x*scipy.mgrid[xslice]
        Y = vs.y*scipy.mgrid[yslice]

        #estimate some start parameters...
        A = dataMean.max() - dataMean.min() #amplitude
        #x0 =  (xslice.start + xslice.stop - 1)/2
        #y0 =  (yslice.start + yslice.stop - 1)/2
        x0 =  X.mean()
        y0 =  Y.mean()

        startParameters = [A, x0, y0, 250/2.35, 250/2.35, dataMean.min(), .001, .001]

        #print dataMean.shape
        #print X.shape

        #estimate errors in data
        nSlices = dataROI.shape[2]
        #sigma = (4 + scipy.sqrt(dataMean))/sqrt(nSlices)
        sigma = scipy.sqrt(self.metadata.CCD.ReadNoise**2 + (self.metadata.CCD.noiseFactor**2)*self.metadata.CCD.electronsPerCount*dataMean/nSlices)/self.metadata.CCD.electronsPerCount
        #do the fit
        #(res, resCode) = FitModel(f_gauss2d, startParameters, dataMean, X, Y)
        (res, cov_x, infodict, mesg, resCode) = FitModelWeighted(self.fitfcn, startParameters, dataMean, sigma, X, Y)

        #print cov_x
        #print infodict['fjac']
        #print mesg
        #print resCode
        #return GaussianFitResult(res, self.metadata, (xslice, yslice, zslice), resCode)
        fitErrors=None
        try:
            fitErrors = scipy.sqrt(scipy.diag(cov_x)*(infodict['fvec']*infodict['fvec']).sum()/(len(dataMean.ravel())- len(res)))
        except Exception as e:
            pass
        return GaussianFitResult(res, self.metadata, (xslice, yslice, zslice), resCode, fitErrors)

    def FromPoint(self, x, y, z=None, roiHalfSize=5, axialHalfSize=15):
        if (z is None): # use position of maximum intensity
            z = self.data[x,y,:].argmax()
	
        x = round(x)
        y = round(y)
	
        return self[max((x - roiHalfSize), 0):min((x + roiHalfSize + 1),self.data.shape[0]), 
                    max((y - roiHalfSize), 0):min((y + roiHalfSize + 1), self.data.shape[1]), 
                    max((z - axialHalfSize), 0):min((z + axialHalfSize + 1), self.data.shape[2])]
        

#so that fit tasks know which class to use
FitFactory = GaussianFitFactory
