
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter

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

#Data sampled at 360/second
samplingFreq = 360

text_file = open("data.txt", "r")
lines = text_file.readlines()

dataArray = { "time": [], "mlII":[], "v5": [] }

counter = 0;
#get values and time for each line
for x in lines:
    x = x.strip().replace("\t","")
    tempval = x.split(" ")
    for x in tempval:
        if x == "":
            tempval.remove(x)
    dataArray["v5"].append(float(tempval[2]))
    dataArray["time"].append(float(tempval[0]))
    dataArray["mlII"].append(float(tempval[1]))
    counter = counter + 1

dataArray["mlII"] = butter_bandpass_filter(dataArray["mlII"], 0.5, 2, samplingFreq, 3)

plt.plot(dataArray["time"][:3000], dataArray["v5"][:3000])
plt.show()
