
import collections
import sys

from pyhdf.HDF import *
from pyhdf.V import *
from pyhdf.VS import *

import h5py
import numpy as np
#import scipy as sp


from HDFDataset import HDFDataset
from Utilities import Utilities


class HDFGroup:
    def __init__(self):
        self.m_id = ""
        self.m_datasets = collections.OrderedDict()
        self.m_attributes = collections.OrderedDict()


    def copy(self, gp):
        self.copyAttributes(gp)
        for k, ds in gp.m_datasets.items():
            newDS = self.addDataset(ds.m_id)
            newDS.copy(ds)

    def copyAttributes(self, gp):
        for k,v in gp.m_attributes.items():
            self.m_attributes[k] = v


    def addDataset(self, name):
        ds = None
        if not self.hasDataset(name):
            ds = HDFDataset()
            ds.m_id = name
            self.m_datasets[name] = ds
        return ds

    def hasDataset(self, name):
        return (name in self.m_datasets)

    def getDataset(self, name):
        if self.hasDataset(name):
            return self.m_datasets[name]
        ds = HDFDataset()
        ds.m_id = name
        self.m_datasets[name] = ds
        return ds


    # Generates Head attributes
    # ToDo: This should get generated from contect file instead
    def getTableHeader(self, name):
        if name != "None":
            cnt = 1
            ds = self.getDataset(name)
            for item in ds.m_columns:
                self.m_attributes["Head_"+str(cnt)] = name + " 1 1 " + item
                cnt += 1



    def printd(self):
        print("Group:", self.m_id)
        #print("Sensor Type:", self.m_sensorType)
        print("Frame Type:", self.m_attributes["FrameType"])
        for k in self.m_attributes:
            print("Attribute:", k, self.m_attributes[k])
        #    attr.printd()
        #for gp in self.m_groups:
        #    gp.printd()
        for k in self.m_datasets:
            ds = self.m_datasets[k]
            ds.printd()


    def read(self, f):
        name = f.name[f.name.rfind("/")+1:]
        #if len(name) == 0:
        #    name = "/"
        self.m_id = name

        #print("Attributes:", [k for k in f.attrs.keys()])
        for k in f.attrs.keys():
            if type(f.attrs[k]) == np.ndarray:
                self.m_attributes[k] = f.attrs[k]
            else: # string
                self.m_attributes[k] = f.attrs[k].decode("utf-8")
        for k in f.keys():
            item = f.get(k)
            if isinstance(item, h5py.Group):
                print("HDFGroup should not contain groups")
            elif isinstance(item, h5py.Dataset):
                #print("Item:", k)
                ds = HDFDataset()
                self.m_datasets[k] = ds
                ds.read(item)


    def write(self, f):
        #print("Group:", self.m_id)
        f = f.create_group(self.m_id)
        for k in self.m_attributes:
            f.attrs[k] = np.string_(self.m_attributes[k])
        for key,ds in self.m_datasets.items():
            #f.create_dataset(ds.m_id, data=np.asarray(ds.m_data))
            ds.write(f)


    # Writing to HDF4 file using PyHdf
    def writeHDF4(self, v, vs):
        print("Group:", self.m_id)
        name = self.m_id[:self.m_id.find("_")]
        if sys.version_info[0] < 3:
            #vg = v.create(self.m_id.encode('utf-8'))
            vg = v.create(name.encode('utf-8'))
        else:
            #vg = v.create(self.m_id)
            vg = v.create(name)

        for k in self.m_attributes:
            attr = vg.attr(k)
            attr.set(HC.CHAR8, self.m_attributes[k])

        for key,ds in self.m_datasets.items():
            #f.create_dataset(ds.m_id, data=np.asarray(ds.m_data))
            ds.writeHDF4(vg, vs)


    # Returns the minimum TimeTag2 value
    def getStartTime(self, time=sys.maxsize):
        if self.hasDataset("TIMETAG2"):
            ds = self.getDataset("TIMETAG2")
            if ds.m_data is not None:
                #print(ds.m_data.dtype)
                tt2 = float(ds.m_data["NONE"][0])
                t = Utilities.timeTag2ToSec(tt2)
                if t < time:
                    time = t
        return time

    # Process timer using TimeTag2 values
    def processTIMER(self, time):
        if self.hasDataset("TIMER"):
            ds = self.getDataset("TIMER")
            tt2DS = self.getDataset("TIMETAG2")
            if ds.m_data is not None:
                #print("Time:", time)
                #print(ds.m_data)
                for i in range(0, len(ds.m_data)):
                    tt2 = float(tt2DS.m_data["NONE"][i])
                    t = Utilities.timeTag2ToSec(tt2)
                    ds.m_data["NONE"][i] = t - time
                #print(ds.m_data)


    # Looks like Prosoft recalculates TIMER by subtracting all values by t0 then adds an offset
    # Note: if could be better to use TimeTag2 values?
    def processTIMERProsoft(self):
        if self.hasDataset("TIMER"):
            ds = self.getDataset("TIMER")
            t0 = ds.m_data["NONE"][0]
            t1 = ds.m_data["NONE"][1]
            #offset = t1 - t0

            min0 = t1 - t0
            total = len(ds.m_data["NONE"])
            #print("test avg")
            for i in range(1, total):
                num = ds.m_data["NONE"][i] - ds.m_data["NONE"][i-1]
                if num < min0:
                    min0 = num
            offset = min0
            #print("min:",min0)


            '''
            avg = 0
            total = len(ds.m_data["NONE"])
            print("test avg")
            for i in range(1, total):
                num = ds.m_data["NONE"][i] - ds.m_data["NONE"][i-1]
                if self.m_id == "ES":
                    print(num)
                avg += num
            avg /= total
            offset = avg
            '''
            
            #print("offset",offset)
            if self.m_attributes["FrameType"] == "LightAncCombined":
                offset += 0.1
            elif self.m_attributes["FrameType"] == "ShutterLight" or \
                self.m_attributes["FrameType"] == "ShutterDark":
                offset += 0.3
            if ds.m_data is not None:
                #print("Time:", time)
                #print(ds.m_data)
                for i in range(0, len(ds.m_data)):
                    ds.m_data["NONE"][i] += -t0 + offset
                #print(ds.m_data)

