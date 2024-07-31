import sys, time
from scipy.signal import welch, butter, sosfilt
try:
    import plotext as plt
    using_plotext = True
except:
    print('To enable live plotting please install plotext')
    using_plotext = False
from betaBoard_interface import betaBoard
import numpy as np
from icecream import ic

# Settings
CHANNEL = 3 # r2: ch3; r1: ch2
# THRESHOLD = int(-65*1.35)
# THRESHOLD = int(-55)
# THRESHOLD = int(-37)
THRESHOLD = int(-30)
# THRESHOLD = int(-30)
# THRESHOLD = int(-55 * 1.9)
print(f'Threshold: {THRESHOLD*3.3/2**12*1e3:.2f} mV')

# open connection
bb = betaBoard(sys.argv[1])
bb.set_trigger_status(0) # disable triggering for now

# clear betaBoard buffer
bb.read_messages()
bb.pulses = list()

# prepare board
bb.set_threshold(THRESHOLD)
bb.set_channel(CHANNEL)
bb.set_led_status(0) # disable LED

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
f.write(f'# Trigger Threshold: {bb.get_threshold()}\n')
f.write(f'# Comment: {comment}\n')
f.write(f'# Channel: {bb.get_channel()}\n')
f.write(f'# LED status: {bb.get_led_status()}\n')
f.write(f'# Board ID: {bb.get_uid()}\n')

f.flush()

bb.read_messages()
bb.pulses = list()

bb.set_trigger_status(1)

# record pulses
start = time.time()
pulse_count = 0
while True:
    bb.read_messages()

    for block_idx, timestamp, overflow, waveform, trigger_counter, block_edge_trigger in bb.pulses:
        pulse_count += 1
        print()
        print(f'time={timestamp*1e-6:.6f}s overflow={overflow} cnt={pulse_count} ->rate={pulse_count/(time.time()-start):.5f}Hz duration={(time.time()-start)/60:.1f}min')

        # TODO: fixme; This is only a hack while the firmware does not guarantee fixed length waveforms yet
        if len(waveform) < pre+post:
            waveform = np.array( list(waveform) + list(np.zeros(pre + post - len(waveform))) )
            print('short waveform')
            ic(block_idx, timestamp, overflow, waveform, trigger_counter, block_edge_trigger)
        if len(waveform) > pre+post:
            waveform = waveform[:pre+post]
            print('long_waveform')
            ic(block_idx, timestamp, overflow, waveform, trigger_counter, block_edge_trigger)

        csv_line = f'{block_idx},{timestamp},{int(overflow)},{trigger_counter},{",".join(map(str, waveform))}\n'
        f.write(csv_line)
        f.flush()

        if using_plotext:
            plt.clear_figure()
            plt.plot_size(height=15)
            plt.plot(waveform * bb.ADCC_TO_V)
            plt.show()

    bb.pulses = []
