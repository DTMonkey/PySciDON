
import sys

import numpy as np
import scipy as sp


import HDFRoot
#import HDFGroup
#import HDFDataset

from Utilities import Utilities


class ProcessL2s:

    # recalculate TimeTag2 to follow GPS UTC time
    @staticmethod
    def processGPSTime(node):
        sec = 0

        for gp in node.m_groups:
            #if gp.m_id.startswith("GPS"):
            if gp.hasDataset("UTCPOS"):
                ds = gp.getDataset("UTCPOS")
                sec = Utilities.utcToSec(ds.m_data["NONE"][0])
                #print("GPS UTCPOS:", ds.m_data["NONE"][0], "-> sec:", sec)
                #print(secToUtc(sec))

        for gp in node.m_groups:
            #if not gp.m_id.startswith("GPS"):
            if not gp.hasDataset("UTCPOS"):
                dsTimer = gp.getDataset("TIMER")
                if dsTimer is not None:
                    dsTimeTag2 = gp.getDataset("TIMETAG2")
                    for x in range(dsTimeTag2.m_data.shape[0]):
                        v = dsTimer.m_data["NONE"][x] + sec
                        dsTimeTag2.m_data["NONE"][x] = Utilities.secToTimeTag2(v)


    @staticmethod
    def interpolateL2s(xData, xTimer, yTimer, newXData, kind='linear'):
        for k in xData.m_data.dtype.names:
            if k == "Datetag" or k == "Timetag2":
                continue
            #print(k)
            x = list(xTimer)
            new_x = list(yTimer)
            y = np.copy(xData.m_data[k]).tolist()
            if kind == 'cubic':
                newXData.m_columns[k] = Utilities.interpSpline(x, y, new_x)
            else:
                newXData.m_columns[k] = Utilities.interp(x, y, new_x, kind)


    # Converts a sensor group into the format used by Level 2s
    # The sensor dataset is renamed (e.g. ES -> ES_hyperspectral)
    # The separate DATETAG, TIMETAG2 datasets are combined into the sensor dataset
    @staticmethod
    def convertGroup(group, datasetName, newGroup, newDatasetName):
        sensorData = group.getDataset(datasetName)
        dateData = group.getDataset("DATETAG")
        timeData = group.getDataset("TIMETAG2")

        newSensorData = newGroup.addDataset(newDatasetName)

        # Datetag and Timetag2 columns added to sensor dataset
        newSensorData.m_columns["Datetag"] = dateData.m_data["NONE"].tolist()
        newSensorData.m_columns["Timetag2"] = timeData.m_data["NONE"].tolist()

        # Copies over the dataset
        for k in sensorData.m_data.dtype.names:
            #print("type",type(esData.m_data[k]))
            newSensorData.m_columns[k] = sensorData.m_data[k].tolist()
        newSensorData.columnsToDataset()


    # Preforms time interpolation to match xData to yData
    @staticmethod
    def interpolateData(xData, yData):
        print("Interpolate Data")

        # Interpolating to itself
        if xData is yData:
            return True

        #xDatetag= xData.m_data["Datetag"].tolist()
        xTimetag2 = xData.m_data["Timetag2"].tolist()

        #yDatetag= yData.m_data["Datetag"].tolist()
        yTimetag2 = yData.m_data["Timetag2"].tolist()


        # Convert TimeTag2 values to seconds to be used for interpolation
        xTimer = []
        for i in range(len(xTimetag2)):
            xTimer.append(Utilities.timeTag2ToSec(xTimetag2[i]))
        yTimer = []
        for i in range(len(yTimetag2)):
            yTimer.append(Utilities.timeTag2ToSec(yTimetag2[i]))

        if not Utilities.isIncreasing(xTimer):
            print("xTimer does not contain strictly increasing values")
            return False
        if not Utilities.isIncreasing(yTimer):
            print("yTimer does not contain strictly increasing values")
            return False

        xData.m_columns["Datetag"] = yData.m_data["Datetag"].tolist()
        xData.m_columns["Timetag2"] = yData.m_data["Timetag2"].tolist()


        #if Utilities.hasNan(xData):
        #    print("Found NAN 1")

        # Perform interpolation
        ProcessL2s.interpolateL2s(xData, xTimer, yTimer, xData, 'cubic')
        xData.columnsToDataset()
        

        #if Utilities.hasNan(xData):
        #    print("Found NAN 2")
        #    exit

        return True


    # interpolate GPS to match ES using linear interpolation
    @staticmethod
    def interpolateGPSData(node, gpsGroup):
        print("Interpolate GPS Data")

        if gpsGroup is None:
            print("WARNING, gpsGroup is None")
            return

        refGroup = node.getGroup("Reference")
        esData = refGroup.getDataset("ES_hyperspectral")

        # GPS
        # Creates new gps group with Datetag/Timetag2 columns appended to all datasets
        gpsTimeData = gpsGroup.getDataset("UTCPOS")
        gpsCourseData = gpsGroup.getDataset("COURSE")
        gpsLatPosData = gpsGroup.getDataset("LATPOS")
        gpsLonPosData = gpsGroup.getDataset("LONPOS")
        gpsMagVarData = gpsGroup.getDataset("MAGVAR")
        gpsSpeedData = gpsGroup.getDataset("SPEED")

        newGPSGroup = node.getGroup("GPS")
        newGPSCourseData = newGPSGroup.addDataset("COURSE")
        newGPSLatPosData = newGPSGroup.addDataset("LATPOS")
        newGPSLonPosData = newGPSGroup.addDataset("LONPOS")
        newGPSMagVarData = newGPSGroup.addDataset("MAGVAR")
        newGPSSpeedData = newGPSGroup.addDataset("SPEED")

        newGPSCourseData.m_columns["Datetag"] = esData.m_data["Datetag"].tolist()
        newGPSCourseData.m_columns["Timetag2"] = esData.m_data["Timetag2"].tolist()
        newGPSLatPosData.m_columns["Datetag"] = esData.m_data["Datetag"].tolist()
        newGPSLatPosData.m_columns["Timetag2"] = esData.m_data["Timetag2"].tolist()
        newGPSLonPosData.m_columns["Datetag"] = esData.m_data["Datetag"].tolist()
        newGPSLonPosData.m_columns["Timetag2"] = esData.m_data["Timetag2"].tolist()
        newGPSMagVarData.m_columns["Datetag"] = esData.m_data["Datetag"].tolist()
        newGPSMagVarData.m_columns["Timetag2"] = esData.m_data["Timetag2"].tolist()
        newGPSSpeedData.m_columns["Datetag"] = esData.m_data["Datetag"].tolist()
        newGPSSpeedData.m_columns["Timetag2"] = esData.m_data["Timetag2"].tolist()


        # Convert GPS UTC time values to seconds to be used for interpolation
        xTimer = []
        for i in range(gpsTimeData.m_data.shape[0]):
            xTimer.append(Utilities.utcToSec(gpsTimeData.m_data["NONE"][i]))

        # Convert ES TimeTag2 values to seconds to be used for interpolation
        yTimer = []
        for i in range(esData.m_data.shape[0]):
            yTimer.append(Utilities.timeTag2ToSec(esData.m_data["Timetag2"][i]))


        # Interpolate by time values
        ProcessL2s.interpolateL2s(gpsCourseData, xTimer, yTimer, newGPSCourseData, 'linear')
        ProcessL2s.interpolateL2s(gpsLatPosData, xTimer, yTimer, newGPSLatPosData, 'linear')
        ProcessL2s.interpolateL2s(gpsLonPosData, xTimer, yTimer, newGPSLonPosData, 'linear')
        ProcessL2s.interpolateL2s(gpsMagVarData, xTimer, yTimer, newGPSMagVarData, 'linear')
        ProcessL2s.interpolateL2s(gpsSpeedData, xTimer, yTimer, newGPSSpeedData, 'linear')


        newGPSCourseData.columnsToDataset()
        newGPSLatPosData.columnsToDataset()
        newGPSLonPosData.columnsToDataset()
        newGPSMagVarData.columnsToDataset()
        newGPSSpeedData.columnsToDataset()


    # Interpolates datasets so they have common time coordinates
    @staticmethod
    def processL2s(node):

        ProcessL2s.processGPSTime(node)

        root = HDFRoot.HDFRoot()
        root.copyAttributes(node)
        root.m_attributes["PROCESSING_LEVEL"] = "2s"
        root.m_attributes["DEPTH_RESOLUTION"] = "0.1 m"

        esGroup = None
        gpsGroup = None
        liGroup = None
        ltGroup = None
        for gp in node.m_groups:
            #if gp.m_id.startswith("GPS"):
            if gp.hasDataset("UTCPOS"):
                print("GPS")
                gpsGroup = gp
            elif gp.hasDataset("ES") and gp.m_attributes["FrameType"] == "ShutterLight":
                print("ES")
                esGroup = gp
            elif gp.hasDataset("LI") and gp.m_attributes["FrameType"] == "ShutterLight":
                print("LI")
                liGroup = gp
            elif gp.hasDataset("LT") and gp.m_attributes["FrameType"] == "ShutterLight":
                print("LT")
                ltGroup = gp

        refGroup = root.addGroup("Reference")
        sasGroup = root.addGroup("SAS")
        if gpsGroup is not None:
            gpsGroup2 = root.addGroup("GPS")


        #ProcessL2s.interpolateGPSData(root, esGroup, gpsGroup)
        #ProcessL2s.interpolateSASData(root, liGroup, ltGroup)

        #ProcessL2s.interpolateData(root, liGroup, ltGroup, esGroup)
        #ProcessL2s.interpolateGPSData2(root, esGroup, gpsGroup)

        ProcessL2s.convertGroup(esGroup, "ES", refGroup, "ES_hyperspectral")        
        ProcessL2s.convertGroup(liGroup, "LI", sasGroup, "LI_hyperspectral")
        ProcessL2s.convertGroup(ltGroup, "LT", sasGroup, "LT_hyperspectral")

        esData = refGroup.getDataset("ES_hyperspectral")
        liData = sasGroup.getDataset("LI_hyperspectral")
        ltData = sasGroup.getDataset("LT_hyperspectral")

        # Find dataset with lowest amount of data
        esLength = len(esData.m_data["Timetag2"].tolist())
        liLength = len(liData.m_data["Timetag2"].tolist())
        ltLength = len(ltData.m_data["Timetag2"].tolist())

        interpData = None
        if esLength < liLength and esLength < ltLength:
            print("Interpolating to ES")
            interpData = esData
        elif liLength < ltLength:
            print("Interpolating to LI")
            interpData = liData
        else:
            print("Interpolating to LT")
            interpData = ltData

        #interpData = liData # Testing against Prosoft
        
        # Perform time interpolation
        if not ProcessL2s.interpolateData(esData, interpData):
            return None
        if not ProcessL2s.interpolateData(liData, interpData):
            return None
        if not ProcessL2s.interpolateData(ltData, interpData):
            return None

        ProcessL2s.interpolateGPSData(root, gpsGroup)

        return root
