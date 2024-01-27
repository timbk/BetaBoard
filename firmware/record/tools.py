import numpy as np

def log_average(x, y, scale):
    """
        x, y: x and y data (x must be ascending)
        scale: maximum values per decade in x
    """
    assert len(x) == len(y)
    outX = []
    outY = []
    idx = 0

    while idx<len(x):
        collect_count = int(np.ceil(x[idx]/scale)) if x[idx]>0 else 1

        outX.append(np.mean(x[idx:idx+collect_count]))
        outY.append(np.mean(y[idx:idx+collect_count]))
        idx += collect_count
    return outX, outY 
