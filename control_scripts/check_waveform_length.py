from betaBoard_interface import betaBoard
import sys

bb = betaBoard(sys.argv[1])

bb.set_threshold(-40)

while True:
    bb.read_messages()

    for block_idx, timestamp, overflow, waveform, trigger_counter, block_edge_trigger in bb.pulses:
        print(block_idx, timestamp, len(waveform), block_edge_trigger)
    bb.pulses = []
