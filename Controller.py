
import collections
import os
#import sys

from PyQt4.QtCore import pyqtSlot
from PyQt4 import QtGui

import h5py
#import numpy as np
#import scipy as sp

from CalibrationFileReader import CalibrationFileReader
#from RawFileReader import RawFileReader
from HDFRoot import HDFRoot
#from HDFGroup import HDFGroup
#from HDFDataset import HDFDataset

from Utilities import Utilities

from ProcessL1a import ProcessL1a
from ProcessL1b import ProcessL1b
from ProcessL2 import ProcessL2
from ProcessL2s import ProcessL2s
from ProcessL3a import ProcessL3a
from ProcessL4 import ProcessL4


class Controller:
    @staticmethod
    def generateContext(calibrationMap):
        for key in calibrationMap:
            cf = calibrationMap[key]
            if cf.m_id == "SATHED0150":
                cf.m_instrumentType = "Reference"
                cf.m_media = "Air"
                cf.m_measMode = "Surface"
                cf.m_frameType = "ShutterDark"
                cf.m_sensorType = "ES"
            elif cf.m_id == "SATHLD0151":
                cf.m_instrumentType = "SAS"
                cf.m_media = "Air"
                cf.m_measMode = "VesselBorne"
                cf.m_frameType = "ShutterDark"
                cf.m_sensorType = "LI"
            elif cf.m_id == "SATHLD0152":
                cf.m_instrumentType = "SAS"
                cf.m_media = "Air"
                cf.m_measMode = "VesselBorne"
                cf.m_frameType = "ShutterDark"
                cf.m_sensorType = "LT"
            elif cf.m_id == "SATHSE0150":
                cf.m_instrumentType = "Reference"
                cf.m_media = "Air"
                cf.m_measMode = "Surface"
                cf.m_frameType = "ShutterLight"
                cf.m_sensorType = "ES"
            elif cf.m_id == "SATHSL0151":
                cf.m_instrumentType = "SAS"
                cf.m_media = "Air"
                cf.m_measMode = "VesselBorne"
                cf.m_frameType = "ShutterLight"
                cf.m_sensorType = "LI"
            elif cf.m_id == "SATHSL0152":
                cf.m_instrumentType = "SAS"
                cf.m_media = "Air"
                cf.m_measMode = "VesselBorne"
                cf.m_frameType = "ShutterLight"
                cf.m_sensorType = "LT"
            elif cf.m_id == "SATSAS0052":
                cf.m_instrumentType = "SAS"
                cf.m_media = "Air"
                cf.m_measMode = "VesselBorne"
                cf.m_frameType = "LightAncCombined"
                cf.m_sensorType = "None"
            elif cf.m_id == "$GPRMC":
                cf.m_instrumentType = "GPS"
                cf.m_media = "Not Required"
                cf.m_measMode = "Not Required"
                cf.m_frameType = "Not Required"
                cf.m_sensorType = "None"

    @staticmethod
    def processCalibration(calPath):
        print("ReadCalibrationFile")
        calibrationMap = CalibrationFileReader.read(calPath)
        #calibrationMap = CalibrationFileReader.readSip("cal2013.sip")
        print("calibrationMap:", list(calibrationMap.keys()))
        Controller.generateContext(calibrationMap)
        return calibrationMap


    @staticmethod
    def processL1a(root, fp, calibrationMap):
        (dirpath, filename) = os.path.split(fp)
        filename = os.path.splitext(filename)[0]
        print("ProcessL1a")
        #root = RawFileReader.readRawFile("data.raw", calibrationMap)
        #generateContext(root)
        #print("HDFFile:")
        #root.printd()
        fp = os.path.join(dirpath, filename + ".raw")
        #root = root.processL1a(calibrationMap, fp)
        root = ProcessL1a.processL1a(calibrationMap, fp)
        root.writeHDF5(os.path.join(dirpath, filename + "_L1a.hdf"))
        #fp = os.path.join(dirpath, filename + "_L1a.hdf4")
        #if os.path.exists(fp):
        #    os.remove(fp)
        #root.writeHDF4(fp)
        return root

    def processL1b(root, fp, calibrationMap):
        (dirpath, filename) = os.path.split(fp)
        filename = os.path.splitext(filename)[0]
        print("ProcessL1b")
        root = HDFRoot.readHDF5(os.path.join(dirpath, filename + "_L1a.hdf"))
        #print("HDFFile:")
        #root.printd()
        #root = root.processL1b(calibrationMap)
        root = ProcessL1b.processL1b(root, calibrationMap)
        root.writeHDF5(os.path.join(dirpath, filename + "_L1b.hdf"))
        return root

    @staticmethod
    def processL2(root, fp):
        (dirpath, filename) = os.path.split(fp)
        filename = os.path.splitext(filename)[0]
        print("ProcessL2")
        root = HDFRoot.readHDF5(os.path.join(dirpath, filename + "_L1b.hdf"))
        #root.processTIMER()
        #root = root.processL2()
        root = ProcessL2.processL2(root)
        root.writeHDF5(os.path.join(dirpath, filename + "_L2.hdf"))
        return root

    @staticmethod
    def processL2s(root, fp):
        (dirpath, filename) = os.path.split(fp)
        filename = os.path.splitext(filename)[0]
        print("ProcessL2s")
        root = HDFRoot.readHDF5(os.path.join(dirpath, filename + "_L2.hdf"))
        #processGPSTime(root)
        #root = root.processL2s()
        root = ProcessL2s.processL2s(root)
        #root.printd()
        root.writeHDF5(os.path.join(dirpath, filename + "_L2s.hdf"))
        return root

    @staticmethod
    def processL3a(root, fp):
        (dirpath, filename) = os.path.split(fp)
        filename = os.path.splitext(filename)[0]
        print("ProcessL3a")
        root = HDFRoot.readHDF5(os.path.join(dirpath, filename + "_L2s.hdf"))
        #root = root.processL3a()
        root = ProcessL3a.processL3a(root)
        root.writeHDF5(os.path.join(dirpath, filename + "_L3a.hdf"))
        return root

    @staticmethod
    def processL4(root, fp):
        (dirpath, filename) = os.path.split(fp)
        filename = os.path.splitext(filename)[0]
        print("ProcessL4")
        root = HDFRoot.readHDF5(os.path.join(dirpath, filename + "_L3a.hdf"))
        #root = root.processL4()
        root = ProcessL4.processL4(root)
        if root is not None:
            Utilities.plotReflectance(root, filename)
            root.writeHDF5(os.path.join(dirpath, filename + "_L4.hdf"))
        return root

    @staticmethod
    def processAll(fp, calibrationMap):
        root = HDFRoot()
        root = Controller.processL1a(root, fp, calibrationMap)
        root = Controller.processL1b(root, fp, calibrationMap)
        root = Controller.processL2(root, fp)
        root = Controller.processL2s(root, fp)
        root = Controller.processL3a(root, fp)
        root = Controller.processL4(root, fp)
        #root = HDFRoot.readHDF5(os.path.join(dirpath, filename + "_L3a.hdf"))

    @staticmethod
    def processDirectory(path, calibrationMap):
        for (dirpath, dirnames, filenames) in os.walk(path):
            for name in filenames:
                #print("infile:", name)
                if os.path.splitext(name)[1].lower() == ".raw":
                    Controller.processAll(os.path.join(dirpath, name), calibrationMap)
            break
