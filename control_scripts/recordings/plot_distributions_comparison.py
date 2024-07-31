'''
plot the pulse height distribution for multiple measurements
Usage: python plot_distributions_comparison.py <serial_device>
Where <serial_device> is:
    Windows: COM?
    Linux: /dev/ttyACM?
    Mac: /dev/tty.usbmodem?
    (The ? is a number)
'''
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from icecream import ic
import sys

def load_recording(fname):
    """ load a file with recorded pulses """
    data = np.genfromtxt(fname, delimiter=',', comments='#')

    with open(fname, 'r') as f:
        sample_rate = float(f.readline().split(' ')[3])
        firmware_version = ' '.join(f.readline().split(' ')[3:])
        trigger_threshold = float(f.readline().split(' ')[3])
        comment = ' '.join(f.readline().split(' ')[2:])

    return data, [sample_rate, firmware_version, trigger_threshold, comment]

def calculate_threshold_scan(idata):
    # calculate measurement duration
    timestamps = idata[:,1] * 1e-6
    duration = timestamps[-1] - timestamps[0]

    # get waveforms
    waveforms = idata[:,3:] * 3.3 / 2**12

    # extract peak height
    peak_heights = np.min(waveforms, axis=1)

    # calculate histogram
    bins = np.arange(-300, 0, 3) * 3.3/2**12
    hist, bin_edges = np.histogram(peak_heights, bins=bins)
    ic(hist.shape, bin_edges.shape)

    return hist, bin_edges, duration

if __name__ == '__main__':
    # load files
    data = [load_recording(fname) for fname in sys.argv[1:]]

    # histogram
    plt.figure()
    for idx, ((idata, [sample_rate, firmware_version, trigger_threshold, comment])) in enumerate(data):
        hist, bin_edges, duration = calculate_threshold_scan(idata)

        comment = comment.replace('\n', ' ')
        label = f'Sample rate: {sample_rate*1e-3:.1f} kSps threshold: {trigger_threshold}ADCC duration: {duration:.3f}s\n{comment}'

        plt.bar(-1*(bin_edges[1:]+bin_edges[:-1])/2, hist/duration, bin_edges[1]-bin_edges[0], label=label, alpha=0.3, fc=f'C{idx}')
        plt.step(-1*bin_edges[1:], hist/duration, bin_edges[1]-bin_edges[0], c=f'C{idx}')

    plt.xlabel('Pulse height [$V_\\text{amplified}$]')
    plt.yscale('log')
    plt.ylabel('Rate per bin [Hz]')
    plt.legend()
    plt.grid()

    # cumulative
    plt.figure()
    for idx, ((idata, [sample_rate, firmware_version, trigger_threshold, comment])) in enumerate(data):
        hist, bin_edges, duration = calculate_threshold_scan(idata)

        comment = comment.replace('\n', ' ')
        label = f'Sample rate: {sample_rate*1e-3:.1f} kSps threshold: {trigger_threshold}ADCC duration: {duration:.3f}s\n{comment}'

        hist_acc = [sum(hist[:i]) for i in range(len(hist))]

        plt.plot(-1*(bin_edges[1:]+bin_edges[:-1])/2, hist_acc/duration, c=f'C{idx}', label=label)

    plt.xlabel('Pulse height [$V_\\text{amplified}$]')
    plt.yscale('log')
    plt.ylabel('Rate above threshold [Hz]')
    plt.legend()
    plt.grid()

    plt.show()
