import serial
import numpy as np

class betaBoard:
    ADCC_TO_V = 3.3 / 2**12

    def __init__(self, device:str):
        """
            Constructor
            device: (str) Address of the USB serial device
                Linux:   '/dev/ttyACMX'
                Mac:     '/dev/tty.usbmodemXXX'
                Windows: 'COMX'
                X = Random number
        """
        self.conn = serial.Serial(device, timeout=0.1)
        self.pulses = []

        self.response_queue = []

    def _clear(self):
        ''' clear input buffer '''
        while True:
            response = self.conn.readline()
            if len(response) == 0:
                break
            self.response_queue.append(response)

    def _execute_command(self, command_char, params=[], ignore_response=False):
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

    def get_version(self):
        return self._execute_command('v')

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
        response = self._execute_command('B' if filtered else 'b')
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
    import sys
    try:
        import plotext as plt
        using_plotext = True
    except:
        import matplotlib.pyplot as plt
        using_plotext = False

    bb = betaBoard(sys.argv[1]) 

    samples = []
    N = 4
    for i in range(N):
        print(f'{i} / {N}', end='\r')
        samples.append( bb.get_data_dump(False) * bb.ADCC_TO_V )
    print()
    samples = np.array(samples).flatten()

    bin_edges, hist= np.histogram(samples, bins=40)

    plt.plot(hist, bin_edges)
    plt.xlabel('Amp output [V]')
    plt.show()

    print(f'Mean: {np.mean(samples):.4f}V; Std: {np.std(samples):.4f}V')
