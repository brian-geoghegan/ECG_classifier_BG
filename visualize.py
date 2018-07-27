
import os
import matplotlib.pyplot as plt
import math
import operator
import time
from scipy import signal
from collections import OrderedDict
import requests

# List to capture features of heartBeats
featureList = []
# Data sampled at 360/second
samplingFreq = 360

heartBeatTimes = []


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

def getTrainingData():
	finalECGdata = OrderedDict()
	patientCounter = 0
	for filename in os.listdir("."):
		tempEcgData = OrderedDict()
		if filename.startswith("data"):
			patientCounter = patientCounter + 1
			ecg_data_file = open(filename, "r")
			data = ecg_data_file.readlines()
			for x in data:
				x = x.strip().replace("\t","")
				tempval = x.split(" ")
				for x in tempval:
					if x == "":
						tempval.remove(x)
				time = tempval[0]
				mlIIvalue = tempval[1]
				tempEcgData.update({float(time): float(mlIIvalue), "Patient": float(patientCounter)})
			tempEcgData.popitem(last=False)
		finalECGdata.update(tempEcgData)
	return finalECGdata
	
#get class for each beat
def getTrainingClassifications():
	tempClassifications = []
	for filename in os.listdir("."):
		if filename.startswith("annotation"):
			annotation_file = open(filename, "r")
			annotations = annotation_file.readlines()
			for x in annotations:
				x = x.strip().replace("\t","")
				tempval = x.split(" ")
				for x in tempval:
					if x == "":
						tempval.remove(x)
				tempClassifications.append(tempval[2])
	del tempClassifications[0]
	return tempClassifications

#Begin R Peak extraction from mlII
def RPeakExtraction(capture):
	tempRPeaks = OrderedDict()
	singleRPeakMap = OrderedDict()
	
	for key, value in ecgData.items():	 
		#Begin capturing values over the threshold
		if(value > mlIIAverageValue):
			singleRPeakMap.update({str(key): float(value)})
			capture = True
		
		#if the values go below threshold - store the largest value
		#Clear the singleRPeakMap for the next RPeak, set capture to false
		elif (capture == True):
			RPeak = max(singleRPeakMap.items(), key=operator.itemgetter(1))
			heartBeatTimes.append(float(RPeak[0]))
			tempRPeaks.update({str(RPeak[0]): float(RPeak[1])})
			singleRPeakMap.clear()
			capture = False
	return tempRPeaks
	
# RR- Intervals
# now for each value in the list
# for each time in heartBeatTimes, subtract previous time from current time
def getRRIntervals():
	tempRRIntervalList = []
	for i in range(len(heartBeatTimes)- 1):
		tempRRIntervalList.append(heartBeatTimes[i+1] - heartBeatTimes[i])
	counter = 0
	return tempRRIntervalList
	
ecgData = getTrainingData()
classifications = getTrainingClassifications()
#Normalized value of mlII
mlIIAverageValue = math.sqrt(sum(ecgData.values())*sum(ecgData.values())) / len(ecgData)
print("Average value: " + str(mlIIAverageValue))
RPeaksMap = RPeakExtraction(False)

#have r_peaks - get average heartbeats per min - feature
#30 minutes of ECG data
averageBeatsPerMin = len(RPeaksMap)//30
print("Beats per min: " + str(averageBeatsPerMin))

#remove first R Peak as it has missing data
RRIntervalList = getRRIntervals()

#remove first beats from data - these are incomplete feature wise
for key in RPeaksMap.keys():
	print("The key : " + key)
	if float(key) < 0.6:
		del RPeaksMap[key]
	break
print (len(RPeaksMap))
print (len(RRIntervalList))
print (len(classifications))

for key,value in RPeaksMap.items():
	time = key
	RPeakValue = value
	RRInterval = RRIntervalList[counter]
	classification = classifications[counter]
	featureList.append([time, RPeakValue, RRInterval, classification])
	counter = counter + 1

#for time in dataArray["time"]:

#dataArray["mlII"] = bandPassFilter(dataArray["mlII"])
samplesToPlot = 1000
x = list(map(float, ecgData.keys()))[:samplesToPlot]
y = list(ecgData.values())[:samplesToPlot]
plt.plot(x, y)
plt.annotate(featureList[0][3], xy=(float(featureList[0][0]), featureList[0][1]))
plt.annotate(featureList[1][3], xy=(float(featureList[1][0]), featureList[1][1]))
plt.annotate(featureList[2][3], xy=(float(featureList[2][0]), featureList[2][1]))
plt.show()

