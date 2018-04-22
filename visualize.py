
import matplotlib.pyplot as plt
import math
import operator
import random
import time
from scipy import signal
from collections import OrderedDict

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
	sortedVotes = sorted(classVotes.iteritems(), key=operator.itemgetter(1), reverse=True)
	return sortedVotes[0][0]
 
def getAccuracy(testSet, predictions):
	correct = 0
	for x in range(len(testSet)):
		if testSet[x][-1] == predictions[x]:
			correct += 1
	return (correct/float(len(testSet))) * 100.0

def splitData(split, featureList, trainingSet, testSet):
    for x in range(len(featureList)-1):
	for y in range(3):
	    featureList[x][y] = float(featureList[x][y])
        if random.random() < split:
            trainingSet.append(featureList[x])
        else:
            testSet.append(featureList[x])

# List to capture features of heartBeats
featureList = []
# Data sampled at 360/second
samplingFreq = 360

# Needs to be updated to read through multiple files
ecg_data_file = open("data.txt", "r")
annotation_file = open("annotation.txt", "r")

data = ecg_data_file.readlines()
annotations = annotation_file.readlines()
classifications = []
ecgData = OrderedDict()

# Get values and time for each line
for x in data:
    x = x.strip().replace("\t","")
    tempval = x.split(" ")
    for x in tempval:
        if x == "":
            tempval.remove(x)
    time = tempval[0]
    mlIIvalue = tempval[1]
    ecgData.update({float(time): float(mlIIvalue)})

#get class for each beat
for x in annotations:
    x = x.strip().replace("\t","")
    tempval = x.split(" ")
    for x in tempval:
        if x == "":
            tempval.remove(x)
    classifications.append(tempval[2])

#remove first heartbeat - incomplete feature data
del classifications[0]

#Normalized value of mlII
mlIIAverageValue = math.sqrt(sum(ecgData.values())*sum(ecgData.values())) / len(ecgData)
print("Average value: " + str(mlIIAverageValue))

#Working dictionaries for capturing R Peaks
singleRPeakMap = OrderedDict()
RPeaksMap = OrderedDict()
capture = False
heartBeatTimes = []

#Begin R Peak extraction from mlII
for key, value in ecgData.items():   
    #Begin capturing values over the threshold
    if(value > mlIIAverageValue):
        singleRPeakMap.update({str(key): float(value)})
	capture = True
    
    #if the values go below threshold - store the largest value
    #Clear the singleRPeakMap for the next RPeak, set capture to false
    elif (capture == True):
	RPeak = max(singleRPeakMap.iteritems(), key=operator.itemgetter(1))
	heartBeatTimes.append(float(RPeak[0]))
	RPeaksMap.update({str(RPeak[0]): float(RPeak[1])})
	singleRPeakMap.clear()
	capture = False

#have r_peaks - get average heartbeats per min - feature
#30 minutes of ECG data
averageBeatsPerMin = len(RPeaksMap)//30
print("Beats per min: " + str(averageBeatsPerMin))

#remove first R Peak as it has missing data

RRIntervalList = []

# RR- Intervals
# now for each value in the list
# for each time in heartBeatTimes, subtract previous time from current time
for i in range(len(heartBeatTimes)- 1):
    RRIntervalList.append(heartBeatTimes[i+1] - heartBeatTimes[i])

#remove first beats from data - these are incomplete feature wise
for key in RPeaksMap.keys():
    print("The key : " + key)
    if float(key) < 0.6:
        del RPeaksMap[key]
    break

counter = 0
#Set feature list
for key,value in RPeaksMap.items():
    time = key
    RPeakValue = value
    RRInterval = RRIntervalList[counter]
    classification = classifications[counter]
    featureList.append([time, RPeakValue, RRInterval, classification])
    counter = counter + 1

#for time in dataArray["time"]:


#split feature list into training and test data
trainingSet = []
testSet = []
split = 0.67
splitData(split, featureList, trainingSet, testSet)
predictions=[]
k = 3
for x in range(len(testSet)):
	print(testSet[0])
	neighbors = getNeighbors(trainingSet, testSet[x], k)
	result = getResponse(neighbors)
	predictions.append(result)
	print('> predicted=' + repr(result) + ', actual=' + repr(testSet[x][-1]))
accuracy = getAccuracy(testSet, predictions)
print('Accuracy: ' + repr(accuracy) + '%')

#dataArray["mlII"] = bandPassFilter(dataArray["mlII"])
samplesToPlot = 1000

'''
x = list(map(float, ecgData.keys()))[:samplesToPlot]
y = list(ecgData.values())[:samplesToPlot]

plt.plot(x, y)
plt.annotate(featureList[0][3], xy=(float(featureList[0][0]), featureList[0][1]))
plt.annotate(featureList[1][3], xy=(float(featureList[1][0]), featureList[1][1]))
plt.annotate(featureList[2][3], xy=(float(featureList[2][0]), featureList[2][1]))
plt.show()
'''
