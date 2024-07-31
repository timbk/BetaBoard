import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch, iirnotch, lfilter, butter, sosfilt
from icecream import ic

## I think my way of scaling only wokrs on DF1 structure (otherwise the intermediate values seem to explode)

def sos_custom(b, a, data):
    assert len(a) == len(b), f'len(a)={len(a)}, len(b)={len(b)}'
    assert len(a) == 3

    print('a', a)
    print('b', b)

    fbuf = [0, 0, 0]
    for x in data:
        # calculate
        fbuf = [0] + fbuf[:-1]
        fbuf[0] = x*a[0] + fbuf[1]*a[1]*(-1)# + fbuf[2]*a[2]*(-1)
        yield b[0]*fbuf[0] + b[1]*fbuf[1]# + b[2]*fbuf[2]
        # shift fbuf

def sos_c_reimp(array):
    a1=-0.96906742; b0=0.98453371; b1=-0.98453371;

    last_value = 0;

    for i in range(len(array)):
        current_value = array[i] - a1*last_value;
        tmp = current_value*b0 + last_value*b1;
        last_value = current_value
        yield tmp

def sos_fixed_point2(array):
    # a0 = 1; a1=-0.96906742; b0=0.98453371; b1=-0.98453371; # values for HPF with 0.01 relative freq
    # b0 = 0.99686824; b1 = -0.99686824; a0 = 1.        ; a1 = -0.99373647 # values for HPF with 0.002 relative freq
    b0, b1, b2, a0, a1, a2 = butter(1, 0.02, btype='highpass', output='sos')[0]

    scale = 2**16
    a0 = int(a0*scale)
    a1 = int(a1*scale)
    b0 = int(b0*scale)
    b1 = int(b1*scale)

    ic(a0, a1, b0, b1)

    xp = 0; yp = 0;
    for i, x in enumerate(array):
        y = int( (b0*x + b1*xp - a1*yp) / a0 )
        yield y
        if i < 30:
            print(i, x, y)
        yp = y
        xp = x

def sos_fixed_point(array):
    a1=-0.96906742; b0=0.98453371; b1=-0.98453371; # values for HPF with 0.01 relative freq

    scale = 1 # 2**24
    a0 = 1 *scale
    a1 = a1*scale
    b0 = b0*scale
    b1 = b1*scale

    print(a0, a1)
    print(b0, b1)


    xp = 0 # x_{n-1}
    yp = 0 # y_{n-1}
    for x in array:
        y = (b0*x + b1*xp - a1*yp) / a0
        yield y
        xp = x
        yp = y

    ''' DF2
    last_value = 0
    for i in range(len(array)):
        current_value = a0*array[i] - a1*last_value;
        tmp = current_value*b0 + last_value*b1;
        last_value = current_value
        # print(tmp, current_value)
        yield tmp, current_value
    '''

N = int(1e6)

FS = 1000e3

# hpf = butter(1, 1000/FS, btype='highpass', output='sos')
hpf = butter(1, 0.01, btype='highpass', output='sos')
ic(hpf)

noise = (np.random.uniform(0, 1, N) * 2**8).astype(np.int32)
filtered = sosfilt(hpf, noise)
filtered2 = list(sos_custom(hpf[0][:3], hpf[0][3:], noise))
# filtered3 = np.array(list(sos_fixed_point(noise))).T
filtered4 = list(sos_fixed_point2(noise))

# plt.figure()
# plt.plot(noise, label='in')
# plt.plot(filtered3[0], label='out')
# plt.plot(filtered3[1], label='hidden')
# plt.legend()
# plt.show()

nperseg = 1024
f, S_n = welch(noise, fs=FS, nperseg=nperseg)
f, S_f = welch(filtered, fs=FS, nperseg=nperseg)
f, S_f2 = welch(filtered2, fs=FS, nperseg=nperseg)
# f, S_f3 = welch(filtered3[0], fs=FS, nperseg=nperseg)
f, S_f4 = welch(filtered4, fs=FS, nperseg=nperseg)

plt.plot(f, S_n, label='input')
plt.plot(f, S_f, label='scipy')
# plt.plot(f, S_f2, ls=':')
plt.plot(f, S_f4, ls=':', label='me')

plt.legend()
plt.grid()

plt.yscale('log')

plt.show()
