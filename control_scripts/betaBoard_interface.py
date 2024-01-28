import serial
import numpy as np

class betaBoard:
    ADCC_TO_V = 3.3 / 2**12

    def __init__(self, device:str, timeout=0.01):
        """
            Constructor
            device: (str) Address of the USB serial device
                Linux:   '/dev/ttyACMX'
                Mac:     '/dev/tty.usbmodemXXX'
                Windows: 'COMX'
                X = Random number
        """
        self.timeout = timeout
        self.conn = serial.Serial(device, timeout=timeout)
        self.pulses = []

        self.response_queue = []
        self.pulses = []

    def _parse_queue(self):
        ''' parse messages in the response queue (not matched to any request) '''
        # for now: all messages are triggers
        for entry in self.response_queue:
            entry = entry.split(' ')

            if entry[0] != 'OT':
                print(f'Warning: Unexpected message start: {repr(entry[0])}')
                continue
            if entry[4] != '#':
                print(f'Warning: Could not find \'#\' at index 4 of OT trigger message')
                continue

            try:
                block_idx = int(entry[1])
                timestamp = int(entry[2])
                overflow = bool(int(entry[3]))
                waveform = np.array([int(i) for i in entry[5:-1]])

                new_data = (block_idx, timestamp, overflow, waveform)
                self.pulses.append(new_data)
            except:
                print(f'Warning: Could not parse integers in OT trigger message')
                continue
        self.response_queue = []

    def _clear(self):
        self.conn.timeout = 0.001

        while True:
            response = self.conn.readline()
            if len(response) == 0:
                break
            self.response_queue.append(response.decode())

        self.conn.timeout = self.timeout

    def read_messages(self):
        ''' clear input buffer '''
        self._clear()
        self._parse_queue()

    def _execute_command(self, command_char, params=[], ignore_response=False, timeout=None):
        """
            Internal macro that sends a command to the device and optionally collects the response
            command_char: The command character. Example: 'v' to retrieve the version
            params: Optional parameters, list of string
            ignore_response: don't parse the response, ignore if none is provided
        """
        assert type(command_char)==str and len(command_char)==1, "command must be a single character"

        self._clear()

        # send command
        for p in params:
            assert type(p) == str
        command = f"{command_char} " + ' '.join(params) + '\r'
        # print(f'sending {repr(command)}')
        self.conn.write(command.encode())

        # receive response if expected
        if not ignore_response:
            if timeout is not None:
                self.conn.timeout = timeout

            while True:
                response = self.conn.readline().decode()
                if len(response) == 0:
                    raise RuntimeError(f'No response or too late response')
                if response[0] == 'E':
                    raise RuntimeError(f'Error to {command_char}: {repr(response)}')
                if response[0] != 'O':
                    raise RuntimeError(f'Unknown response to {command_char}: {repr(response)}')

                if response[1] != command_char:
                    self.response_queue.append(response)
                    continue

                return response[3:]

            self.conn.timeout = self.timeout

    def get_version(self):
        return self._execute_command('v')[:-2]

    def get_waveform_length(self, _set_values=[]):
        """
            retrieve how many samples will be recorded before and after the trigger
            returns: sample_count_before, sample_count_after
        """
        response = self._execute_command('p', _set_values)
        try:
            pre = int(response.split(' ')[0])
            post = int(response.split(' ')[1])
        except:
            raise RuntimeError(f'Malformed response: {repr(response)}')
        return pre, post

    def set_waveform_length(self, pre, post):
        """
            set how many samples will be recorded before and after the trigger
            pre: sample count before
            post: sample count after
            returns: sample_count_before, sample_count_after (read back from device)
        """
        assert type(pre)==int and pre>0, "pre must be positive integer"
        assert type(post)==int and post>0, "post must be positive integer"

        return self.get_waveform_length(_set_values=[str(pre), str(post)])

    def get_ignore_count(self, _set_values=[]):
        response = self._execute_command('i', _set_values)
        try:
            value = int(response.split(' ')[0])
        except:
            raise RuntimeError(f'Malformed response: {repr(response)}')
        return value

    def set_ignore_count(self, ignore_count):
        assert type(ignore_count)==int and ignore_count>0, "ignore_count must be positive integer"
        return self.get_ignore_count([str(ignore_count)])

    def get_threshold(self, _set_values=[]):
        response = self._execute_command('t', _set_values)
        try:
            value = int(response.split(' ')[0])
        except:
            raise RuntimeError(f'Malformed response: {repr(response)}')
        return value

    def set_threshold(self, threshold):
        assert type(threshold)==int, "threshold must be integer"
        if threshold > 0:
            print('Warning: Thresholds are typically negative!')
        return self.get_threshold([str(threshold)])

    def get_trigger_status(self, _set_values=[]):
        response = self._execute_command('T', _set_values)
        try:
            value = int(response.split(' ')[0])
        except:
            raise RuntimeError(f'Malformed response: {repr(response)}')
        return value

    def set_trigger_status(self, trigger_status):
        assert trigger_status in [0, 1]
        return self.get_trigger_status([str(trigger_status)])

    def get_data_dump(self, filtered=True):
        """
            Retrieve an untriggered sequence of samples
            filtered: Set to false to get the values before the high pass filter
            returns: numpy array of samples in ADC counts
        """
        response = self._execute_command('B' if filtered else 'b', timeout=4)
        try:
            samples = response.split(' ')[:-1]
            samples = np.fromiter(map(int, samples), dtype=np.int16)
        except:
            raise RuntimeError(f'Malformed response: {repr(response)}')
        return samples

    def get_sample_rate(self):
        """ Get the sample rate in Hertz """
        response = self._execute_command('s')
        try:
            value = int(response.split(' ')[0])
        except:
            raise RuntimeError(f'Malformed response: {repr(response)}')
        return value

if __name__ == '__main__':
    import sys, time
    from scipy.signal import welch
    try:
        import plotext as plt
        using_plotext = True
    except:
        import matplotlib.pyplot as plt
        using_plotext = False

    bb = betaBoard(sys.argv[1])
    SR = bb.get_sample_rate()
    print(f'sample rate: {SR} Hz')

    samples = []
    N = 1
    for i in range(N):
        print(f'{i} / {N}', end='\r')
        samples.append( bb.get_data_dump(False) * bb.ADCC_TO_V )
    print()
    samples = np.array(samples).flatten()

    bin_edges, hist= np.histogram(samples, bins=40)

    plt.plot_size(height=20)
    plt.plot(hist, bin_edges)
    plt.xlabel('Amp output [V]')
    plt.show()

    if using_plotext:
        plt.clear_figure()

    plt.plot_size(height=20)
    plt.plot(np.arange(len(samples))/SR, samples)
    plt.ylabel('Amp output [V]')
    plt.xlabel('Time [s]')
    plt.show()

    if using_plotext:
        plt.clear_figure()

    plt.plot_size(height=20)
    f, S = welch(samples, fs=SR, nperseg=len(samples))
    plt.plot(f[1:], S[1:])
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Amp output [V]')
    plt.yscale('log')
    plt.xscale('log')
    plt.show()

    print(f'Mean: {np.mean(samples):.4f}V; Std: {np.std(samples):.4f}V')

    bb.set_threshold(-48)
    while True:
        bb.read_messages()

        for block_idx, timestamp, overflow, waveform in bb.pulses:
            print()
            print(f'time={timestamp*1e-6:.6f}s overflow={overflow}')

            plt.clear_figure()
            plt.plot_size(height=15)
            plt.plot(waveform * bb.ADCC_TO_V)
            plt.show()

        bb.pulses = []
