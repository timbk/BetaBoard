# filter coefficients obtained through scipy:
from scipy.signal import butter, lfilter, freqz
import numpy as np

b, a = butter(1, 0.01, fs=1, btype='low', analog=False)

print('a', ', '.join(map(str, a)))
print('b', ', '.join(map(str, b)))
print()

scale = 2**24 # must be chosen to not saturate the integer size!!

scale_a = scale / max(a)
scale_b = scale / max(b)

total_scale = np.round(scale_b / scale_a)

b = np.round(b*scale_b).astype(np.int64)
a = np.round(a*scale_a).astype(np.int64)

print('a', ', '.join(map(str, a)))
print('b', ', '.join(map(str, b)))
print(total_scale)
