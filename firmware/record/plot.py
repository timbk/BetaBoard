import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import sosfilt, butter

FS = 200e3
sosp = butter(2, 30e3/FS, btype='low', output='sos')

pulses = []
with open('copied_20240122.txt') as f:
    lines = f.readlines()
    for line in lines:
        if 'V' in line:
            continue

        data = [int(i) for i in line.split(' ')]
        pulses.append(data)
print(len(pulses))

pulses = np.array(pulses).astype(np.float64) * 3.3 / 2**12

plt.figure()
plt.plot(pulses.T)
plt.ylabel('Output voltage [V]')
plt.xlabel('Sample count [1] (200 kHz)')


pulses_filtered = np.array([sosfilt(sosp, data) for data in pulses])
plt.figure()
plt.plot(pulses_filtered.T)
plt.ylabel('Output voltage [V]')
plt.xlabel('Sample count [1] (200 kHz)')

plt.show()

