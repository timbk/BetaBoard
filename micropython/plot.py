import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch
import serial
import sys

ser = serial.Serial(sys.argv[1])

clear = ser.readline()
data = ser.readline().decode()[:-1]

data = data.split(' ')[:-1]

lens = [len(i) == 4 for i in data]
lens = lens[:-1]
assert np.all(lens), str(lens)

data = map(lambda x: int(x, 16), data)
data = list(data)

plt.figure()
plt.plot(data)
plt.xlabel('Samples')


plt.figure()
f, S = welch(data, fs=100000, nperseg=1024*4)
plt.xlabel('f [Hz]')
plt.grid()
plt.plot(f, S)

plt.show()

