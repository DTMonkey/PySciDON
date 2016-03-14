
import collections

from datetime import datetime

import h5py
import numpy as np

class HDFDataset:
    def __init__(self):
        self._id = ""
        self._attributes = collections.OrderedDict()
        self._columns = collections.OrderedDict()
        self._numColumns = 0
        self._data = None
        self._temp = []

    def prnt(self):
        print("Dataset:", self._id)
        for k in self._attributes:
            print(k, self._attributes[k])
        #for x in np.nditer(self._data, flags=['external_loop'], op_flags=['readwrite']):
        #    x[...] *= 2
            #print(x)
        #print(self._data)
        #for d in self._data:
        #    d.prnt()

    def read(self, f):
        name = f.name[f.name.rfind("/")+1:]
        self._id = name
        #print(name)
        self._data = np.array(f)
        cols = f.attrs["COL_NAMES"].split(",")
        for i in range(0, len(cols)):
            self._columns[cols[i]] = i
        self._numColumns = len(self._columns)
        #print(self._columns)
        

    def write(self, f):
        #print(self._id)
        #print(self._columns)
        #print(self._data)
        dset = f.create_dataset(self._id, data=self._data)
        dset.attrs["COL_NAMES"] = ",".join(self._columns.keys())


    def getColumn(self, name):
        return self._columns[name]

    def addColumn(self, name):
        if name not in self._columns:
            self._columns[name] = self._numColumns
            self._numColumns += 1
            

    def processL1a(self, cd, inttime = None):
        #print("FitType:", cd._fitType)
        if cd._fitType == "OPTIC1":
            self.processOPTIC1(cd, False)
        elif cd._fitType == "OPTIC2":
            self.processOPTIC2(cd, False)
        elif cd._fitType == "OPTIC3":
            self.processOPTIC3(cd, False, inttime)
        elif cd._fitType == "OPTIC4":
            self.processOPTIC4(cd, False)
        elif cd._fitType == "THERM1":
            self.processTHERM1(cd)
        elif cd._fitType == "POW10":
            self.processPOW10(cd)
        elif cd._fitType == "POLYU":
            self.processPOLYU(cd)
        elif cd._fitType == "POLYF":
            self.processPOLYF(cd)
        elif cd._fitType == "DDMM":
            self.processDDMM(cd)
        elif cd._fitType == "HHMMSS":
            self.processHHMMSS(cd)
        elif cd._fitType == "DDMMYY":
            self.processDDMMYY(cd)
        elif cd._fitType == "TIME2":
            self.processTIME2(cd)
        elif cd._fitType == "COUNT":
            pass
        elif cd._fitType == "NONE":
            pass
        else:
            print("Unknown Fit Type:", cd._fitType)

    def processOPTIC1(self, cd):
        return

    def processOPTIC2(self, cd, immersed):
        self._data = self._data.astype(float)
        a0 = float(cd._coefficients[0])
        a1 = float(cd._coefficients[1])
        im = float(cd._coefficients[2]) if immersed else 1.0
        y = self.getColumn(cd._id)
        for x in range(self._data.shape[0]):
            self._data[x,y] = im * a1 * (self._data[x,y] - a0)

    def processOPTIC3(self, cd, immersed, inttime):
        self._data = self._data.astype(float)
        a0 = float(cd._coefficients[0])
        a1 = float(cd._coefficients[1])
        im = float(cd._coefficients[2]) if immersed else 1.0
        cint = float(cd._coefficients[3])
        #print(inttime._data.shape[0], self._data.shape[0])
        y = self.getColumn(cd._id)
        #print(cint, aint)
        #print(cd._id)
        for x in range(self._data.shape[0]):
            aint = inttime._data[x, 0]
            v = self._data[x,y]
            self._data[x,y] = im * a1 * (self._data[x,y] - a0) * (cint/aint)
            #if x == 0 and y == 0:
            #    print("" + str(a1) + " * (" + str(v) + " - " + \
            #            str(a0) + ") * (" + str(cint) + "/" + str(aint) + ") = " + str(self._data[x,y]))

    def processOPTIC4(self, cd, immersed):
        self._data = self._data.astype(float)
        a0 = float(cd._coefficients[0])
        a1 = float(cd._coefficients[1])
        im = float(cd._coefficients[2]) if immersed else 1.0
        cint = float(cd._coefficients[3])
        y = self.getColumn(cd._id)
        aint = 1
        for x in range(self._data.shape[0]):
            self._data[x,y] = im * a1 * (self._data[x,y] - a0) * (cint/aint)

    def processTHERM1(self, cd):
        return

    def processPOW10(self, cd, immersed):
        self._data = self._data.astype(float)
        a0 = float(cd._coefficients[0])
        a1 = float(cd._coefficients[1])
        im = float(cd._coefficients[2]) if immersed else 1.0
        y = self.getColumn(cd._id)
        for x in range(self._data.shape[0]):
            self._data[x,y] = im * pow(10, ((self._data[x,y]-a0)/a1))

    def processPOLYU(self, cd):
        self._data = self._data.astype(float)
        y = self.getColumn(cd._id)
        for x in range(self._data.shape[0]):
            num = 0
            for i in range(0, len(cd._coefficients)):
                a = float(cd._coefficients[i])
                num += a * pow(self._data[x,y],i)
            self._data[x,y] = num

    def processPOLYF(self, cd):
        self._data = self._data.astype(float)
        a0 = float(cd._coefficients[0])
        y = self.getColumn(cd._id)
        for x in range(self._data.shape[0]):
            num = a0
            for a in cd._coefficients[1:]:
                num *= (self._data[x,y] - float(a))
            self._data[x,y] = num

    def processDDMM(self, cd):
        return
        #for x in np.nditer(self._data, flags=['external_loop'], op_flags=['readwrite']):
            #s = "{:.2f}".format(x)
            #x[...] = s[:1] + " " + s[1:3] + "\' " + s[3:5] + "\""

    def processHHMMSS(self, cd):
        return
        #for x in range(self._data.shape[0]):
            #for y in range(self._data.shape[1]):
                #s = "{:.2f}".format(self._data[x,y])
                #self._data[x,y] = s[:2] + "/" + s[2:4] + "/" + s[4:]
        #for x in np.nditer(self._data, flags=['external_loop'], op_flags=['readwrite']):
            #print(x)
            #s = "{:.2f}".format(x)
            #x[...] = s[:2] + ":" + s[2:4] + ":" + s[4:6] + "." + s[6:8]

    def processDDMMYY(self, cd):
        return
        #for x in np.nditer(self._data, flags=['external_loop'], op_flags=['readwrite']):
            #s = str(x)
            #x[...] = s[:2] + "/" + s[2:4] + "/" + s[4:]

    def processTIME2(self, cd):
        return
        #for x in np.nditer(self._data, flags=['external_loop'], op_flags=['readwrite']):
            #x[...] = datetime.fromtimestamp(x).strftime("%y-%m-%d %H:%M:%S")

    def processDarkCorrection(self, cd, immersed):
        # L_lightdat = (L_countslightdat - L_caldarkdat) * a * ic * it1/it2
        pass
        
        
