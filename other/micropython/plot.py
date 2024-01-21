import numpy as np
import matplotlib
# matplotlib.use('tkagg') # more stable on mac ??
import matplotlib.pyplot as plt
from scipy.signal import welch, iirnotch, lfilter, butter, sosfilt
import serial
import sys

FS = 1000000

ser = serial.Serial(sys.argv[1])

clear = ser.readline()
data = ser.readline().decode()[:-1]

data = data.split(' ')[:-1]

lens = [len(i) == 4 for i in data]
lens = lens[:-1]
assert np.all(lens), str(lens)

data = map(lambda x: int(x, 16), data)
data = np.array(list(data)) * 3.3 / 2**12

# Apply notch filter
# notch_filter50 = iirnotch(50, 30, FS)
# notch_filter100 = iirnotch(100, 30, FS)
# notch_filter200 = iirnotch(200, 30, FS)
# notch_filter250 = iirnotch(250, 30, FS)
# 
# data_notched = lfilter(*notch_filter50, list(reversed(data)))
# data_notched = lfilter(*notch_filter50, list(reversed(data_notched)))
# data_notched = lfilter(*notch_filter100, data_notched)
# data_notched = lfilter(*notch_filter200, data_notched)
# data_notched = lfilter(*notch_filter250, data_notched)

hpf = butter(1, 3000/FS, btype='highpass', output='sos')
print(hpf)
data_notched = sosfilt(hpf, data)

# data_notched = data

T = np.arange(len(data)) / FS

# data = data[1000:]
# data_notched = data_notched[1000:]
# T = T[1000:]


plt.figure()
plt.plot(T, data)
plt.plot(T, data_notched)

plt.axhline(np.mean(data))
plt.axhline(np.mean(data) - 0.055)
plt.axhline(np.mean(data) - 0.2)
plt.axhline(np.mean(data_notched), c='orange')
plt.axhline(np.mean(data_notched) - 0.055, c='orange')
plt.axhline(np.mean(data_notched) - 0.2, c='orange')

plt.axhline(3.3*750/2**12, c='green')
plt.xlabel('Samples')
plt.grid()


plt.figure()
f, S = welch(data, fs=FS, nperseg=1024*64)
plt.plot(f, S)

f, S = welch(data_notched, fs=FS, nperseg=1024*64)
plt.plot(f, S)

plt.xlabel('f [Hz]')
plt.grid()

plt.show()

