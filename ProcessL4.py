
import collections
import sys

import numpy as np
import scipy as sp

import HDFRoot
#import HDFGroup
#import HDFDataset

from Utilities import Utilities
#from WindSpeedReader import WindSpeedReader

#from config import settings
from ConfigFile import ConfigFile


class ProcessL4:

    # Interpolate to a single column
    @staticmethod
    def interpolateColumn(columns, wl):
        #print("interpolateColumn")

        # Values to return
        return_y = []

        # Column to interpolate to
        new_x = [wl]

        # Copy dataset to dictionary
        #ds.datasetToColumns()
        #columns = ds.columns
        
        # Get wavelength values
        wavelength = []
        for k in columns:
            #print(k)
            wavelength.append(float(k))
        x = np.asarray(wavelength)

        # get the length of a column
        num = len(list(columns.values())[0])

        # Perform interpolation for each row
        for i in range(num):

            values = []
            for k in columns:
                #print("b")
                values.append(columns[k][i])
            y = np.asarray(values)
            
            new_y = sp.interpolate.interp1d(x, y)(new_x)
            return_y.append(new_y[0])

        return return_y



    # Perform meteorological flag checking
    @staticmethod
    def qualityCheckVar(es5Columns, esFlag, dawnDuskFlag, humidityFlag):
        print("qualtiy check")

        # Threshold for significant es
        #v = es5Columns["480.0"][0]
        v = ProcessL4.interpolateColumn(es5Columns, 480.0)[0]
        if v < esFlag:
            print("Quality Check: ES(480.0) =", v)
            return False

        # Masking spectra affected by dawn/dusk radiation
        #v = es5Columns["470.0"][0] / es5Columns["610.0"][0] # Fix 610 -> 680
        v1 = ProcessL4.interpolateColumn(es5Columns, 470.0)[0]
        v2 = ProcessL4.interpolateColumn(es5Columns, 680.0)[0]
        v = v1/v2
        if v < dawnDuskFlag:
            print("Quality Check: ES(470.0)/ES(680.0) =", v)
            return False

        # Masking spectra affected by rainfall and high humidity
        #v = es5Columns["720.0"][0] / es5Columns["370.0"][0]    
        v1 = ProcessL4.interpolateColumn(es5Columns, 720.0)[0]
        v2 = ProcessL4.interpolateColumn(es5Columns, 370.0)[0]
        v = v1/v2
        if v < humidityFlag:
            print("Quality Check: ES(720.0)/ES(370.0) =", v)
            return False

        return True

    # Perform meteorological flag checking with settings from config
    @staticmethod
    def qualityCheck(es5Columns):
        esFlag = float(ConfigFile.settings["fL4SignificantEsFlag"])
        dawnDuskFlag = float(ConfigFile.settings["fL4DawnDuskFlag"])
        humidityFlag = float(ConfigFile.settings["fL4RainfallHumidityFlag"])

        result = ProcessL4.qualityCheckVar(es5Columns, esFlag, dawnDuskFlag, humidityFlag)

        return result


    # Take a slice of a dataset stored in columns
    @staticmethod
    def columnToSlice(columns, start, end):
        newSlice = collections.OrderedDict()
        for k in columns:
            newSlice[k] = columns[k][start:end]
        return newSlice


    @staticmethod
    def calculateReflectance2(root, esColumns, liColumns, ltColumns, newRrsData, newESData, newLIData, newLTData, enableQualityCheck, performNIRCorrection, defaultWindSpeed=0.0, windSpeedColumns=None):

        datetag = esColumns["Datetag"]
        timetag = esColumns["Timetag2"]
        latpos = None
        lonpos = None
        

        esColumns.pop("Datetag")
        esColumns.pop("Timetag2")

        liColumns.pop("Datetag")
        liColumns.pop("Timetag2")

        ltColumns.pop("Datetag")
        ltColumns.pop("Timetag2")

        # remove added LATPOS/LONPOS if added
        if "LATPOS" in esColumns:
            latpos = esColumns["LATPOS"]
            esColumns.pop("LATPOS")
            liColumns.pop("LATPOS")
            ltColumns.pop("LATPOS")
        if "LONPOS" in esColumns:
            lonpos = esColumns["LONPOS"]
            esColumns.pop("LONPOS")
            liColumns.pop("LONPOS")
            ltColumns.pop("LONPOS")

        # Stores the middle element
        date = datetag[int(len(datetag)/2)]
        time = timetag[int(len(timetag)/2)]
        if latpos:
            lat = latpos[int(len(latpos)/2)]
        if lonpos:
            lon = lonpos[int(len(lonpos)/2)]


        #print("Test:")
        #print(date, time, lat, lon)


        # Calculates the lowest 5% (based on Hooker & Morel 2003)
        n = len(list(ltColumns.values())[0])
        x = round(n*5/100)
        if n <= 5:
            x = n


        #print(ltColumns["780.0"])

        # Find the indexes for the lowest 5%
        #lt780 = ltColumns["780.0"]
        lt780 = ProcessL4.interpolateColumn(ltColumns, 780.0)
        index = np.argsort(lt780)
        y = index[0:x]


        # Takes the mean of the lowest 5%
        es5Columns = collections.OrderedDict()
        li5Columns = collections.OrderedDict()
        lt5Columns = collections.OrderedDict()
        windSpeedMean = defaultWindSpeed


        # Checks if the data has NaNs
        hasNan = False
        for k in esColumns:
            v = [esColumns[k][i] for i in y]
            mean = np.nanmean(v)
            es5Columns[k] = [mean]
            if np.isnan(mean):
                hasNan = True
        for k in liColumns:
            v = [liColumns[k][i] for i in y]
            mean = np.nanmean(v)
            li5Columns[k] = [mean]
            if np.isnan(mean):
                hasNan = True
        for k in ltColumns:
            v = [ltColumns[k][i] for i in y]
            mean = np.nanmean(v)
            lt5Columns[k] = [mean]
            if np.isnan(mean):
                hasNan = True

        # Mean of wind speed for data
        if windSpeedColumns is not None:
            v = [windSpeedColumns[i] for i in y]
            mean = np.nanmean(v)
            windSpeedMean = mean
            if np.isnan(mean):
                hasNan = True


        # Exit if detect NaN
        if hasNan:
            print("Error NaN Found")
            return False

        # Test meteorological flags
        if enableQualityCheck:
            if not ProcessL4.qualityCheck(es5Columns):
                return False


        # Calculate Rho_sky
        li750 = ProcessL4.interpolateColumn(li5Columns, 750.0)
        es750 = ProcessL4.interpolateColumn(es5Columns, 750.0)
        #sky750 = li5Columns["750.0"][0]/es5Columns["750.0"][0]
        sky750 = li750[0]/es750[0]


        # ToDo: sunny/wind calculations
        if sky750 > 0.05:
            p_sky = 0.0256
        else:
            # Set wind speed here
            w = windSpeedMean
            p_sky = 0.0256 + 0.00039 * w + 0.000034 * w * w
            #p_sky = 0.0256


        # Add extra information to Rrs dataset
        if not ("Datetag" in newRrsData.columns):
            newRrsData.columns["Datetag"] = [date]
            newRrsData.columns["Timetag2"] = [time]
            if latpos:
                newRrsData.columns["Latpos"] = [lat]
            if lonpos:
                newRrsData.columns["Lonpos"] = [lon]
        else:
            newRrsData.columns["Datetag"].append(date)
            newRrsData.columns["Timetag2"].append(time)
            if latpos:
                newRrsData.columns["Latpos"].append(lat)
            if lonpos:
                newRrsData.columns["Lonpos"].append(lon)


        rrsColumns = {}
                
        # Calculate Rrs
        for k in es5Columns:
            if (k in li5Columns) and (k in lt5Columns):
                if k not in newESData.columns:
                    newESData.columns[k] = []
                    newLIData.columns[k] = []
                    newLTData.columns[k] = []
                    newRrsData.columns[k] = []
                #print(len(newESData.columns[k]))
                es = es5Columns[k][0]
                li = li5Columns[k][0]
                lt = lt5Columns[k][0]
                rrs = (lt - (p_sky * li)) / es
                #esColumns[k] = [es]
                #liColumns[k] = [li]
                #ltColumns[k] = [lt]
                #rrsColumns[k] = [(lt - (p_sky * li)) / es]
                newESData.columns[k].append(es)
                newLIData.columns[k].append(li)
                newLTData.columns[k].append(lt)
                #newRrsData.columns[k].append(rrs)
                rrsColumns[k] = rrs


        # Perfrom near-infrared correction of remove additional contamination from sky/sun glint
        if performNIRCorrection:
            # Get average of Rrs values between 750-800nm
            avg = 0
            num = 0
            for k in rrsColumns:
                if float(k) >= 750 and float(k) <= 800:
                    avg += rrsColumns[k]
                    num += 1
            avg /= num
    
            # Subtract average from each spectra
            for k in rrsColumns:
                rrsColumns[k] -= avg


        for k in rrsColumns:
            newRrsData.columns[k].append(rrsColumns[k])

        return True



    @staticmethod
    def calculateReflectance(root, node, interval, enableQualityCheck, performNIRCorrection, defaultWindSpeed=0.0, windSpeedData=None):
    #def calculateReflectance(esData, liData, ltData, newRrsData, newESData, newLIData, newLTData):


        referenceGroup = node.getGroup("Reference")
        sasGroup = node.getGroup("SAS")

        esData = referenceGroup.getDataset("ES_hyperspectral")
        liData = sasGroup.getDataset("LI_hyperspectral")
        ltData = sasGroup.getDataset("LT_hyperspectral")


        newReflectanceGroup = root.getGroup("Reflectance")
        newRrsData = newReflectanceGroup.addDataset("Rrs")
        newESData = newReflectanceGroup.addDataset("ES")
        newLIData = newReflectanceGroup.addDataset("LI")
        newLTData = newReflectanceGroup.addDataset("LT")
        

        # Copy datasets to dictionary
        esData.datasetToColumns()
        esColumns = esData.columns
        tt2 = esColumns["Timetag2"]
        #esColumns.pop("Datetag")
        #tt2 = esColumns.pop("Timetag2")

        liData.datasetToColumns()
        liColumns = liData.columns
        #liColumns.pop("Datetag")
        #liColumns.pop("Timetag2")

        ltData.datasetToColumns()
        ltColumns = ltData.columns
        #ltColumns.pop("Datetag")
        #ltColumns.pop("Timetag2")

        # remove added LATPOS/LONPOS if added
        #if "LATPOS" in esColumns:
        #    esColumns.pop("LATPOS")
        #    liColumns.pop("LATPOS")
        #    ltColumns.pop("LATPOS")
        #if "LONPOS" in esColumns:
        #    esColumns.pop("LONPOS")
        #    liColumns.pop("LONPOS")
        #    ltColumns.pop("LONPOS")


        if Utilities.hasNan(esData):
            print("Found NAN 1") 
            sys.exit(1)

        if Utilities.hasNan(liData):
            print("Found NAN 2") 
            sys.exit(1)

        if Utilities.hasNan(ltData):
            print("Found NAN 3") 
            sys.exit(1)

        esLength = len(list(esColumns.values())[0])
        ltLength = len(list(ltColumns.values())[0])

        if ltLength > esLength:
            for col in ltColumns:
                col = col[0:esLength]
            for col in liColumns:
                col = col[0:esLength]

        windSpeedColumns=None

        # interpolate wind speed to match sensor time values
        if windSpeedData is not None:
            x = windSpeedData.getColumn("TIMETAG2")[0]
            y = windSpeedData.getColumn("WINDSPEED")[0]
            new_x = esData.data["Timetag2"].tolist()
            new_y = Utilities.interp(x, y, new_x)
            windSpeedData.columns["WINDSPEED"] = new_y
            windSpeedData.columns["TIMETAG2"] = new_x
            windSpeedData.columnsToDataset()
            windSpeedColumns = new_y

        #print("items:", esColumns.values())
        #print(ltLength,resolution)
        start = 0
        #end = 0
        endTime = Utilities.timeTag2ToSec(tt2[0]) + interval
        for i in range(0, len(tt2)):
            time = Utilities.timeTag2ToSec(tt2[i])
            if time > endTime:
                end = i-1
                esSlice = ProcessL4.columnToSlice(esColumns, start, end)
                liSlice = ProcessL4.columnToSlice(liColumns, start, end)
                ltSlice = ProcessL4.columnToSlice(ltColumns, start, end)
                ProcessL4.calculateReflectance2(root, esSlice, liSlice, ltSlice, newRrsData, newESData, newLIData, newLTData, enableQualityCheck, performNIRCorrection, defaultWindSpeed, windSpeedColumns)
                
                start = i
                endTime = time + interval


#        for i in range(0, int(esLength/resolution)):
#            #print(i)
#            start = i*resolution
#            end = start+resolution
#            esSlice = ProcessL4.columnToSlice(esColumns, start, end, i, resolution)
#            liSlice = ProcessL4.columnToSlice(liColumns, start, end, i, resolution)
#            ltSlice = ProcessL4.columnToSlice(ltColumns, start, end, i, resolution)
#
#            ProcessL4.calculateReflectance2(root, esSlice, liSlice, ltSlice, newRrsData, newESData, newLIData, newLTData, enableQualityCheck, defaultWindSpeed, windSpeedColumns)


        newESData.columnsToDataset()
        newLIData.columnsToDataset()
        newLTData.columnsToDataset()
        newRrsData.columnsToDataset()


        return True


    # Calculates Rrs
    @staticmethod
    def processL4(node, windSpeedData=None):

        root = HDFRoot.HDFRoot()
        root.copyAttributes(node)
        root.attributes["PROCESSING_LEVEL"] = "4"

        root.addGroup("Reflectance")

        interval = float(ConfigFile.settings["fL4TimeInterval"])
        enableQualityCheck = int(ConfigFile.settings["bL4EnableQualityFlags"])
        performNIRCorrection = int(ConfigFile.settings["bL4PerformNIRCorrection"])
        defaultWindSpeed = float(ConfigFile.settings["fL4DefaultWindSpeed"])
        #windDirectory = settings["sWindSpeedFolder"].strip('"')

        # Can change time resolution here
        if not ProcessL4.calculateReflectance(root, node, interval, enableQualityCheck, performNIRCorrection, defaultWindSpeed, windSpeedData):
            return None

        return root
