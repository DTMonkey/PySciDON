
import collections
import sys

# For testing HDF4 support with pyhdf
#from pyhdf.HDF import *
#from pyhdf.SD import *
#from pyhdf.V import *
#from pyhdf.VS import *

import h5py
import numpy as np
#import scipy as sp

from HDFGroup import HDFGroup
from HDFDataset import HDFDataset


class HDFRoot:
    def __init__(self):
        self.id = ""
        self.groups = []
        self.attributes = collections.OrderedDict()


    # Creates a copy
    def copy(self, node):
        self.copyAttributes(node)
        for gp in node.groups:
            newGP = self.addGroup(gp.id)
            newGP.copy(gp)

    def copyAttributes(self, node):
        for k,v in node.attributes.items():
            self.attributes[k] = v


    def addGroup(self, name):
        gp = None
        if not self.hasGroup(name):
            gp = HDFGroup()
            gp.id = name
            self.groups.append(gp)
        return gp

    def hasGroup(self, name):
        for gp in self.groups:
            if gp.id == name:
                return True
        return False

    def getGroup(self, name):
        for gp in self.groups:
            if gp.id == name:
                return gp
        gp = HDFDataset()
        gp.id = name
        self.groups.append(gp)
        return gp


    def printd(self):
        print("Root:", self.id)
        #print("Processing Level:", self.processingLevel)
        #for k in self.attributes:
        #    print("Attribute:", k, self.attributes[k])
        for gp in self.groups:
            gp.printd()


    @staticmethod
    def readHDF5(fp):
        root = HDFRoot()
        with h5py.File(fp, "r") as f:

            # set name to text after last '/'
            name = f.name[f.name.rfind("/")+1:]
            if len(name) == 0:
                name = "/"
            root.id = name

            # Read attributes
            #print("Attributes:", [k for k in f.attrs.keys()])
            for k in f.attrs.keys():
                root.attributes[k] = f.attrs[k].decode("utf-8")
                # Use the following when using h5toh4 converter:
                #root.attributes[k.replace("__GLOSDS", "")] = f.attrs[k].decode("utf-8")
            # Read groups
            for k in f.keys():
                item = f.get(k)
                #print(item)
                if isinstance(item, h5py.Group):
                    gp = HDFGroup()
                    root.groups.append(gp)
                    gp.read(item)
                elif isinstance(item, h5py.Dataset):
                    print("HDFRoot should not contain datasets")

        return root


    # Writing to HDF5 file
    def writeHDF5(self, fp):
        with h5py.File(fp, "w") as f:
            #print("Root:", self.id)
            # Write attributes
            for k in self.attributes:
                f.attrs[k] = np.string_(self.attributes[k])
                # h5toh4 converter requires "__GLOSDS" to be appended
                # to attribute name for it to be recognized correctly:
                #f.attrs[k+"__GLOSDS"] = np.string_(self.attributes[k])
            # Write groups
            for gp in self.groups:
                gp.write(f)

    # Writing to HDF4 file using PyHdf
    def writeHDF4(self, fp):
        try:
            hdfFile = HDF(fp, HC.WRITE|HC.CREATE)
            sd = SD(fp, SDC.WRITE)
            v = hdfFile.vgstart()
            vs = hdfFile.vstart()

            for k in self.attributes:
                #print(k, self.attributes[k])
                attr = sd.attr(k)
                attr.set(SDC.CHAR8, self.attributes[k])

            for gp in self.groups:
                gp.writeHDF4(v, vs)
        except:
            print("HDFRoot Error:", sys.exc_info()[0])
        finally:
            vs.end()
            v.end()
            sd.end()
            hdfFile.close()

