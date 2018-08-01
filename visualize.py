import os
import matplotlib.pyplot as plt
import math
import operator
import time
from scipy import signal
from collections import OrderedDict
import requests
import random

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
	ECGdata = OrderedDict()
	patientCounter = 0
	for filename in os.listdir("./mitdb"):
		tempEcgData = OrderedDict()
		if filename.startswith("data"):
			print(filename)
			patientCounter = patientCounter + 1
			ecg_data_file = open("mitdb/" +filename, "r")
			data = ecg_data_file.readlines()
			for x in data:
				x = x.strip().replace("\t","")
				tempval = x.split(" ")
				for x in tempval:
					if x == "":
						tempval.remove(x)
				time = tempval[0]
				mlIIvalue = tempval[1]
				tempEcgData.update({float(time): float(mlIIvalue)})
			tempEcgData.popitem(last=False)
		ECGdata.update(tempEcgData)
	return ECGdata
	
#get class for each beat
def getTrainingClassifications():
	tempClassifications = []
	for filename in os.listdir("./mitdb"):
		if filename.startswith("annotation"):
			annotation_file = open("mitdb/" + filename, "r")
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
			print(RPeak[0])
			heartBeatTimes.append(float(RPeak[1]))
			tempRPeaks.update({str(RPeak[0]): float(RPeak[1])})
			singleRPeakMap.clear()
			capture = False
	#remove first beats from data - these are incomplete feature wise
	for key in tempRPeaks.keys():
		print("The key : " + key)
		if float(key) < 0.6:
			del tempRPeaks[key]
		break
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

	
def loadDataset(featureList, split, trainingSet=[] , testSet=[]):
	dataset = list(featureList)
	print(featureList[1])
	for x in range(len(featureList)-1):
		for y in range(3):
			featureList[x][y] = float(featureList[x][y])
		if random.random() < split:
			trainingSet.append(featureList[x])
		else:
			testSet.append(featureList[x])
	
def euclideanDistance(instance1, instance2, length):
	distance = 0
	for x in range(length):
		distance += pow((instance1[x] - instance2[x]), 2)
	return math.sqrt(distance)
 
def getNeighbors(trainingSet, testInstance, k):
	distances = []
	length = len(testInstance)-1
	for x in range(len(trainingSet)):
		dist = euclideanDistance(testInstance, trainingSet[x], length)
		distances.append((trainingSet[x], dist))
	distances.sort(key=operator.itemgetter(1))
	neighbors = []
	for x in range(k):
		neighbors.append(distances[x][0])
	return neighbors
 
def getResponse(neighbors):
	classVotes = {}
	for x in range(len(neighbors)):
		response = neighbors[x][-1]
		if response in classVotes:
			classVotes[response] += 1
		else:
			classVotes[response] = 1
	sortedVotes = sorted(classVotes.items(), key=operator.itemgetter(1), reverse=True)
	return sortedVotes[0][0]
 
def getAccuracy(testSet, predictions):
	correct = 0
	for x in range(len(testSet)):
		if testSet[x][-1] == predictions[x]:
			correct += 1
	return (correct/float(len(testSet))) * 100.0

def reportArrhytmia(data):
	url = ""
	req = requests.post(url, data)
	print(req.status_code, r.reason)
   
ecgData = getTrainingData()
classifications = getTrainingClassifications()

# List to capture features of heartBeats
featureList = []
# Data sampled at 360/second
samplingFreq = 360

heartBeatTimes = []
#have r_peaks - get average heartbeats per min - feature

mlIIAverageValue = math.sqrt(sum(ecgData.values())*sum(ecgData.values())) / len(ecgData)

print("Average value: " + str(mlIIAverageValue))


RPeaksMap = RPeakExtraction(False)
RRIntervalList = getRRIntervals()

averageBeatsPerMin = len(RPeaksMap)//30
print("Beats per min: " + str(averageBeatsPerMin))

print (len(RPeaksMap))
print (len(RRIntervalList))
print (len(classifications))

counter = 0

#Get final feature map
for key, value in RPeaksMap.items():
	time = key
	RPeakValue = value
	RRInterval = RRIntervalList[counter]
	classification = classifications[counter]
	featureList.append([time, RPeakValue, RRInterval, classification])
	counter = counter + 1

# prepare data
trainingSet=[]
testSet=[]
split = 0.67
loadDataset(featureList, split, trainingSet, testSet)
# generate predictions
predictions=[]
k = 3
for x in range(len(testSet)):
	neighbors = getNeighbors(trainingSet, testSet[x], k)
	result = getResponse(neighbors)
	predictions.append(result)
	print('> predicted=' + repr(result) + ', actual=' + repr(testSet[x][-1]))
accuracy = getAccuracy(testSet, predictions)
print('Accuracy: ' + repr(accuracy) + '%')
	
	
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

