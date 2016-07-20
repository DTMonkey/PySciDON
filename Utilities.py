
import time
import datetime

import matplotlib.pyplot as plt
import numpy as np
import scipy.interpolate


class Utilities:

    # Converts GPS UTC time to seconds
    # Note: Does not support multiple days
    @staticmethod
    def utcToSec(utc):
        # Use zfill to ensure correct width, fixes bug when hour is 0 (12 am)
        t = str(int(utc)).zfill(6)
        #print(t)
        #print(t[:2], t[2:4], t[4:])
        h = int(t[:2])
        m = int(t[2:4])
        s = int(t[4:])
        return ((h*60)+m)*60+s


    # Converts seconds to TimeTag2
    @staticmethod
    def secToTimeTag2(sec):
        #return float(time.strftime("%H%M%S", time.gmtime(sec)))
        t = sec * 1000
        s, ms = divmod(t, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return float("%d%02d%02d%03d" % (h, m, s, ms))

    # Converts TimeTag2 to seconds
    @staticmethod
    def timeTag2ToSec(tt2):
        t = str(int(tt2)).zfill(9)
        h = int(t[:2])
        m = int(t[2:4])
        s = int(t[4:6])
        ms = int(t[6:])
        #print(h, m, s, ms)
        return ((h*60)+m)*60+s+(float(ms)/1000.0)

    # Converts HDFRoot timestamp attribute to seconds
    @staticmethod
    def timestampToSec(timestamp):
        time = timestamp.split(" ")[3]
        t = time.split(":")
        h = int(t[0])
        m = int(t[1])
        s = int(t[2])
        return ((h*60)+m)*60+s

    # Check if dataset contains NANs
    def detectNan(ds):
        for k in ds.m_data.dtype.fields.keys():
            for x in range(ds.m_data.shape[0]):
                if np.isnan(ds.m_data[k][x]):
                    return True
        return False
        

    # Wrapper for scipy interp1d that works even if
    # values in new_x are outside the range of values in x
    @staticmethod
    def interp(x, y, new_x, kind='linear'):

        #print("t0", len(x), len(y))
        n0 = len(x)-1
        n1 = len(new_x)-1
        if new_x[n1] > x[n0]:
            #print(new_x[n], x[n])
            x.append(new_x[n1])
            y.append(y[n0])
        if new_x[0] < x[0]:
            #print(new_x[0], x[0])
            x.insert(0, new_x[0])
            y.insert(0, y[0])

        # Note: large jumps in time causes NANs to appear
        #print("t1", len(x), len(y))
        #new_y = scipy.interpolate.interp1d(x, y, kind=kind, bounds_error=False)(new_x)
        #new_y = scipy.interpolate.interp1d(x, y, kind=kind, bounds_error=False, fill_value=0.0)(new_x)
        #new_y = scipy.interpolate.interp1d(x, y, kind='linear', bounds_error=False, fill_value=0.0)(new_x)
        new_y = scipy.interpolate.interp1d(x, y, kind=kind, bounds_error=False, fill_value=0.0)(new_x)

        '''
        test = False
        for i in range(len(new_y)):
            if np.isnan(new_y[i]):
                #print("NaN")
                if test:
                    new_y[i] = darkData.m_data[k][darkData.m_data.shape[0]-1]
                else:
                    new_y[i] = darkData.m_data[k][0]
            else:
                test = True
        '''

        return new_y


    # Wrapper for scipy UnivariateSpline interpolation
    # This method does not seem stable unless points are uniform distance apart - results in all Nan output
    @staticmethod
    def interpSpline(x, y, new_x):

        #print("t0", len(x), len(y))
        n0 = len(x)-1
        n1 = len(new_x)-1
        if new_x[n1] > x[n0]:
            #print(new_x[n], x[n])
            x.append(new_x[n1])
            y.append(y[n0])
        if new_x[0] < x[0]:
            #print(new_x[0], x[0])
            x.insert(0, new_x[0])
            y.insert(0, y[0])

        #new_y = scipy.interpolate.interp1d(x, y, kind='quadratic', bounds_error=False, fill_value=0.0)(new_x)
        #new_y = scipy.interpolate.interp1d(x, y, kind='cubic', bounds_error=False, fill_value=0.0)(new_x)
        #new_y = scipy.interpolate.UnivariateSpline(x, y, k=3, s=5e8)(new_x)
        new_y = scipy.interpolate.InterpolatedUnivariateSpline(x, y, k=3)(new_x)

        return new_y



    @staticmethod
    def plotReflectance(root, filename):

        referenceGroup = root.getGroup("Reflectance")
        rrsData = referenceGroup.getDataset("Rrs")

        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 16,
            }

        x = []
        y = []
        for k in [k for k,v in sorted(rrsData.m_data.dtype.fields.items(), key=lambda k: k[1])]:
            x.append(k)
            y.append(rrsData.m_data[k][0])

        plt.plot(x, y, 'k')
        #plt.title('Remote sensing reflectance', fontdict=font)
        #plt.text(2, 0.65, r'$\cos(2 \pi t) \exp(-t)$', fontdict=font)
        plt.xlabel('wavelength (nm)', fontdict=font)
        plt.ylabel('Rrs (sr^{-1})', fontdict=font)

        # Tweak spacing to prevent clipping of ylabel
        plt.subplots_adjust(left=0.15)
        #plt.show()
        plt.savefig('Plots/' + filename + '.png')
        plt.close() # This prevents displaying the polt on screen with certain IDEs

