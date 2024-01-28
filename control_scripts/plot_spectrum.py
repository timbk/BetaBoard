from betaBoard_interface import betaBoard
import sys
# import plotext as plt
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import sosfilt, butter, welch
from tools import log_average

SR = 200e3

def hpf(data):
    sosp = butter(2, 1e3/SR, btype='high', output='sos')
    return sosfilt(sosp, data)

if __name__ == '__main__':
    simulation = np.genfromtxt('amplifier_spice_sim.csv', delimiter=',').T

    bb = betaBoard(sys.argv[1])

    print("recording");
    samples = []
    N = 1
    for i in range(N):
        print(f'{i} / {N}', end='\r')
        samples.append( bb.get_data_dump(False) * bb.ADCC_TO_V )
    print()
    samples = np.array(samples)

    S = []
    Sf = []
    for waveform in samples:
        f, iS = welch(waveform, fs=SR, nperseg=len(waveform))
        S.append(iS)
        f, iS = welch(hpf(waveform), fs=SR, nperseg=len(waveform))
        Sf.append(iS)

    plt.plot(*log_average(f[1:], 1e6*np.sqrt(np.mean(S, axis=0)[1:]), 300), label='Measurement')
    plt.plot(*log_average(f[1:], 1e6*np.sqrt(np.mean(Sf, axis=0)[1:]), 300), label='Measurement + HPF')
    plt.plot(simulation[0], 1e6*simulation[1], label='Simulation')
    # plt.scatter(f[1:], np.sqrt(np.mean(S, axis=0)[1:]))
    # plt.axhline(40e-6)

    plt.xlabel('Frequency [Hz]')
    plt.ylabel('ASD [$\\mu V/\sqrt{\\text{Hz}})$]')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlim(10, 100e3)
    plt.ylim(1, 600)
    plt.grid()
    plt.legend()

    plt.figure()
    plt.plot(samples[0] - np.mean(samples[0]))

    print(f'Mean: {np.mean(samples):.4f}V; Std: {np.std(samples):.4f}V')

    plt.show()
