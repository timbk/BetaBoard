import numpy as np
import scipy.constants as sc

E_K40 = 1.4e6 # eV
m = 0.5e6 # eV
z = 1 # e- charge
ZoA = 0.5 # Z/A charge over atomic number of matter


K = 0.307 # MeV mol/cm**2

gamma = lambda E: E/m+1
beta = lambda E: np.sqrt(1-1/gamma(E)**2)

bethe = lambda E: K*z**2
