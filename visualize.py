
import matplotlib.pyplot as plt
import math

import time
from scipy import signal

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=3):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

def bandPassFilter(originalSignal):
    startFilter = time.time()
    filterOrder = 4;
    lowCutOffFreq = 0.25
    highCutOffFreq = 0.01
    B, A = signal.butter(filterOrder, highCutOffFreq, btype='high', output='ba')
    filteredSignal = signal.filtfilt(B, A, originalSignal, axis=0);
    B, A = signal.butter(filterOrder, lowCutOffFreq, btype='low', output='ba')
    filteredSignal = signal.filtfilt(B, A, filteredSignal, axis=0);
    endFilter = time.time()
    print("Filter Elapsed time", endFilter - startFilter, "Filter order: ", filterOrder)
    return filteredSignal

def get_change(current, previous):
    if current == previous:
        return 100.0
    try:
        measurement = abs(current - previous)/previous
        percent = measurement*100
        return percent
    except ZeroDivisionError:
         return 0


#Data sampled at 360/second
samplingFreq = 360

text_file = open("data.txt", "r")
lines = text_file.readlines()

dataArray = { }



#get values and time for each line
for x in lines:
    x = x.strip().replace("\t","")
    tempval = x.split(" ")
    for x in tempval:
        if x == "":
            tempval.remove(x)
    time = tempval[0]
    mlIIvalue = tempval[1]
    dataArray.update({str(time): float(mlIIvalue)})

#Normalized value of mlII
mlIIAverageValue = math.sqrt(sum(dataArray.values())*sum(dataArray.values())) / len(dataArray)
mlII_R_peaks = { }

#Begin feature extraction from mlII
for key, value in dataArray.items():
    currReading = value
    if(currReading > mlIIAverageValue):
        mlII_R_peaks.update({str(key): float(value)})

print(mlII_R_peaks)
#for time in dataArray["time"]:

#dataArray["mlII"] = bandPassFilter(dataArray["mlII"])
samplesToPlot = 1000
plt.plot(dataArray["time"][:samplesToPlot], dataArray["mlII"][:samplesToPlot])


plt.show()
