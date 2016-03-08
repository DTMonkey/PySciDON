
import collections

import h5py
import numpy as np

from HDFDataset import HDFDataset

class HDFGroup:
    def __init__(self):
        self._id = ""
        self._attributes = collections.OrderedDict()
        self._groups = []
        self._datasets = []

    def prnt(self):
        print("Group:", self._id)
        for k in self._attributes:
            print("Attribute:", k, self._attributes[k])
        #    attr.prnt()
        for gp in self._groups:
            gp.prnt()
        for ds in self._datasets:
            ds.prnt()

    def hasDataset(self, name):
        for ds in self._datasets:
            if ds._id == name:
                return True
        return False

    def getDataset(self, name):
        for ds in self._datasets:
            if ds._id == name:
                return ds
        ds = HDFDataset()
        ds._id = name
        self._datasets.append(ds)
        return ds
            

    def read(self, f):
        name = f.name[f.name.rfind("/")+1:]
        if len(name) == 0:
            name = "/"
        #self._id = bytes(name, "utf-8")
        self._id = name

        #print("Attributes:", [k for k in f.attrs.keys()])
        for k in f.attrs.keys():
            self._attributes[k] = f.attrs[k]
        for k in f.keys():
            item = f.get(k)
            if isinstance(item, h5py.Group):
                gp = HDFGroup()
                self._groups.append(gp)
                gp.read(item)
            elif isinstance(item, h5py.Dataset):
                ds = HDFDataset()
                self._datasets.append(ds)
                ds.read(item)
            
        #if isinstance(item, h5py.File):
        #if isinstance(item, h5py.Group):
        #if isinstance(item, h5py.Dataset):
        

    def write(self, f):
        #print("Group:", self._id)
        if self._id != "/":
            f = f.create_group(self._id)
        for k in self._attributes:
            f.attrs[k] = self._attributes[k]
        for gp in self._groups:
            gp.write(f)
        for ds in self._datasets:
            #f.create_dataset(ds._id, data=np.asarray(ds._data))
            ds.write(f)


    def processL1a(self, cf):
        inttime = None
        for cd in cf._data:
            if cd._type == "INTTIME":
                print("Process INTTIME")
                ds = self.getDataset("INTTIME")
                ds.processL1a(cd)
                inttime = ds
            
        for cd in cf._data:
            if self.hasDataset(cd._type) and cd._type != "INTTIME":
                #print("Dataset:", cd._type)
                ds = self.getDataset(cd._type)
                ds.processL1a(cd, inttime)


        

