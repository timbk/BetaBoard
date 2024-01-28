import sys, time
from scipy.signal import welch
try:
    import plotext as plt
    using_plotext = True
except:
    print('To enable live plotting please install plotext')
    using_plotext = False
from betaBoard_interface import betaBoard
import numpy as np

# Settings
THRESHOLD = -48

# open connection
bb = betaBoard(sys.argv[1])

# get board config
SR = bb.get_sample_rate()
print(f'sample rate: {SR} Hz')

pre, post = bb.get_waveform_length()

firmware_version = bb.get_version()
print(f'version: {firmware_version}')

comment = input('Comment: ')

# open output file
fname = 'pulses_'+time.strftime("%Y%m%d-%H%M%S")+'.csv'
f = open('recordings/' + fname, 'w')

# write file header
f.write(f'# Sample rate: {SR}\n')
f.write(f'# Firmware version: {firmware_version}\n')
f.write(f'# Trigger Threshold: {THRESHOLD}\n')
f.write(f'# Comment: {comment}\n')

f.flush()

# record pulses
bb.set_threshold(THRESHOLD)
while True:
    bb.read_messages()

    for block_idx, timestamp, overflow, waveform in bb.pulses:
        print()
        print(f'time={timestamp*1e-6:.6f}s overflow={overflow}')

        # TODO: fixme; This is only a hack while the firmware does not guarantee fixed length waveforms yet
        if len(waveform) < pre+post:
            waveform = np.array( list(waveform) + list(np.zeros(pre + post - len(waveform))) )

        csv_line = f'{block_idx}, {timestamp}, {int(overflow)}, {", ".join(map(str, waveform))} \n'
        f.write(csv_line)
        f.flush()

        if using_plotext:
            plt.clear_figure()
            plt.plot_size(height=15)
            plt.plot(waveform * bb.ADCC_TO_V)
            plt.show()

    bb.pulses = []
