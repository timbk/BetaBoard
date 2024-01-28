import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import sosfilt, butter
import sys

FS = 200e3
sosp = butter(2, 30e3/FS, btype='low', output='sos')

# fname = 'copied_20240122.txt'
# fname = 'copied_20240124_usb_ref3033.txt'
fname = sys.argv[1]

pulses = []
with open(fname) as f:
    lines = f.readlines()
    for line in lines:
        if 'V' in line:
            continue
        print(line)
        data = [int(i) for i in line.split('#')[1].split(' ')[1:]]
        pulses.append(data)
print(len(pulses))

for i, j in enumerate(pulses):
    print(i, len(j))

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

