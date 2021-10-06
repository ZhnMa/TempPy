"""
Python file for Individual Project - Server Data processing

Read data from data file generated earlier

Developed by: Zhaonan Ma el20z2m@leeds.ac.uk

28 Sep 2021
"""

import matplotlib.pyplot as pl
import numpy as np

dataFile = open("data32.txt", "rb")
data = dataFile.read()
dataFile.close()
print(data)

data = list(data)
if data[0] < 240 or data[0] > 243:  # the first one needs to be a configuration byte
    raise ValueError('Incomplete Data Flow: data[0] = {}, needs to be a configuration byte'.format(data[0]))

'''
Configuration:
0xf3 243: 32 bits, default, both temperature and humidity with decimal points
0xf1 241: 16 bits, both temperature and humidity without decimal points
oxf0 240: 16 bits, only one of both with decimal points then another

Pin information:
0xex 224 + x: x: 0bxxxx four pins
------
New form:
Data = [f1, p1, [t1, t2, ...], [h1, h2, ...], f2, p2, [t1, t2, ...], ...]
f: configuration 
p: pin info
t: temperature
h: humidity
'''
# make a dictionary according to above
configDict = {225: 'Pin1', 226: 'Pin2', 227: 'Pin1, Pin2', 228: 'Pin3', 229: 'Pin1, Pin3', 230: 'Pin2, Pin3',
              231: 'Pin1, Pin2, Pin3', 232: 'Pin4', 233: 'Pin1, Pin4', 234: 'Pin2, Pin4', 235: 'Pin1, Pin2, Pin4',
              236: 'Pin3, Pin4', 237: 'Pin1, Pin3, Pin4', 238: 'Pin2, Pin3, Pin4', 239: 'Pin1, Pin2, Pin3, Pin4',
              240: '16 Bits with Decimal Points', 241: '16 Bits without Decimal Points', 243: '32 Bits Full Data'}

# PROCESS, format data into 'Data'
Data = []
Temp = []
Humi = []
for each in data:
    if each >= 244:  # incorrect signal, raise an error
        raise ValueError('Incorrect Signal: data: {}'.format(each))
    elif 240 <= each < 244:
        if not Data:  # empty
            config = each
            Data.append(config)
        else:
            # configuration changed, start new process
            Data.append(Temp)
            Data.append(Humi)
            Temp = []
            Humi = []
            config = each
            Data.append(config)
            Data.append(Data[-4])  # pin
        oneData = 0  # next value is data
    elif 224 <= each < 240:  # pin info byte
        if len(Data) == 1:
            Data.append(each)
        else:
            # pin changed, start new process
            if each in [225, 226, 228, 232]:
                pin = 1  # one pin
            elif each in [227, 229, 233, 230, 234, 236]:
                pin = 2  # 2 pins
            elif each in [238, 237, 235, 231]:
                pin = 3  # 3 pins
            elif each == 239:
                pin = 4  # 4 pins
            else:
                raise ValueError('Wrong Pin Info: {}'.format(each))
            Data.append(Temp[:-pin])
            Data.append(Humi[:-pin])
            Temp = Temp[-pin:]
            Humi = Humi[-pin:]
            Data.append(config)
            Data.append(each)
        oneData = 0  # next value is data
    else:  # data, separate two data and keep them continual
        # 32 bits || 16 bits with decimals, !!might face mal-position issue
        if config == 243 or config == 240:
            if oneData == 0 or oneData == 2:  # decimal points byte
                deci = each / 10
                oneData += 1
            elif oneData == 1:  # temperature integer byte
                temp = each
                temp += deci
                Temp.append(temp)
                oneData += 1
            elif oneData == 3:  # humidity integer byte
                humi = each
                humi += deci
                Humi.append(humi)
                oneData = 0
            else:  # wrong value
                raise IndexError('Incorrect Index Value: oneData = {}'.format(oneData))
        elif config == 241:  # 16 bits, both data with no decimal points
            if oneData == 0:  # first the temperature
                Temp.append(each)
                oneData += 1
            elif oneData == 1:  # then the humidity
                Humi.append(each)
                oneData = 0
            else:  # wrong value, raise an error
                raise IndexError('Incorrect Index Value: oneData = {}'.format(oneData))
        else:  # no such a configuration type, raise an error
            raise ValueError('Incorrect Configuration Number: config = {}'.format(config))
# include the last data
if data[-1] < 224:  # in case there is a final pin change
    Data.append(Temp)
    Data.append(Humi)
print(Data)

###############################################################
#  PLOT
xStart = 0
ax1 = pl.subplot(2, 1, 1)
pl.ylabel('Temperature / `C')
pl.ylim([25, 35])  # make it [0, 50] for general limit
pl.grid()
ax2 = pl.subplot(2, 1, 2)
pl.xlabel('Sampling Times')
pl.ylabel('Humidity / %')
pl.ylim([5, 100])
pl.grid()
colours = ['#CD0000', '#9932CC', '#EEAD0E', '#228B22']
for i in range(0, len(Data), 1):
    if Data[i] in [225, 226, 228, 232]:  # one pin
        if len(Data[i + 1]) != len(Data[i + 2]):
            raise IndexError('Incorrect Data length: Temp: {0}, Humi: {1}'.format(len(Data[i + 1]), len(Data[i + 2])))
        leng = len(Data[i + 1])
        # make annotations
        ax1.plot([xStart, xStart], [0, 50], 'r--')
        ax1.text(xStart, 34, configDict[Data[i-1]])
        ax1.text(xStart, 33, configDict[Data[i]])
        ax2.plot([xStart, xStart], [0, 100], 'r--')
        # Temperature
        xAxis = np.linspace(xStart, xStart + leng - 1, leng)
        ax1.scatter(xAxis, Data[i + 1])
        # Humidity
        xAxis = np.linspace(xStart, xStart + leng - 1, leng)
        ax2.scatter(xAxis, Data[i + 2])
        # renew starting point
        xStart += leng
    else:
        if Data[i] in [227, 229, 233, 230, 234, 236]:  # 2 pins
            pinNum = 2
        elif Data[i] in [238, 237, 235, 231]:
            pinNum = 3
        elif Data[i] == 239:
            pinNum = 4
        else:
            continue
        p = 0
        ax1.plot([xStart, xStart], [0, 50], 'r--')
        ax1.text(xStart, 34, configDict[Data[i - 1]])
        ax1.text(xStart, 33, configDict[Data[i]])
        ax2.plot([xStart, xStart], [0, 100], 'r--')
        for d in range(0, len(Data[i + 1]), 1):
            ax1.scatter(xStart, Data[i + 1][d], color=colours[p])
            ax2.scatter(xStart, Data[i + 2][d], color=colours[p])
            p += 1
            if p == pinNum:  # odd
                xStart += 1
                p = 0

pl.show()
