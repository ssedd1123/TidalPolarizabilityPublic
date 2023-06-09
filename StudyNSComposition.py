from decimal import Decimal
from TidalLove.TidalLoveWrapper import TidalLoveWrapper
import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt
import pandas as pd
import tempfile
import math
import time


def LoadSkyrmeFile(filename):
    df = pd.read_csv(filename, index_col=0)
    return df.fillna(0)

def PressureComposition(ax, eos, trans_dens, eos_name, filename):
    df = LoadSkyrmeFile(filename)
    row = df.loc[eos_name]
    rho0 = 0.16

    trans_dens = [10*rho0] + trans_dens + [1e-9]
    trans_dens = np.array(trans_dens)
    trans_pressure = eos.GetPressure(trans_dens, 0)

    start = time.time()
    max_pressure = row['PCentral']
    max_density = opt.newton(lambda rho: eos.GetPressure(rho, 0) - max_pressure, x0=0.16)
    min_density = opt.newton(lambda rho: eos.GetPressure(rho, 0) - 1e-8, x0=1e-5)

    with TidalLoveWrapper(eos) as tlove:
        tlove.density_checkpoint = np.linspace(min_density, max_density, 200).tolist()
        result = tlove.FindMass(1.4)
        mass = result['Checkpoint_mass']
        radius = result['Checkpoint_radius']
        pressure = tlove.checkpoint

    density = []
    for pre in pressure:
        try:
            if pre < 5:
                density.append(opt.newton(lambda rho: eos.GetPressure(rho, 0) - pre, x0=pre, maxiter=100))
            else:
                density.append(opt.newton(lambda rho: eos.GetPressure(rho, 0) - pre, x0=5*0.16, maxiter=100))
        except Exception as error:
            density.append(0)

    data = pd.DataFrame.from_dict({'mass':mass, 'radius':radius, 'pressure':pressure, 'density':density})
    color = ['r', 'b', 'g', 'orange', 'b', 'pink']
    labels = ['', 'Crustal EOS', 'Electron gas', 'Skyrme'] + ['']*(len(trans_dens) - 4)
    data = data[data['pressure'] > 1e-9]
    for num, trans_den in enumerate(trans_pressure):
        data_subrange = data[data['pressure'] < trans_den]
        ax[0].plot(data_subrange['radius'], data_subrange['pressure'], color=color[num], label=labels[-num-1], marker='o')
        ax[1].plot(data_subrange['radius'], data_subrange['mass'], color=color[num], label=labels[-num-1], marker='o')
        ax[2].plot(data_subrange['radius'], data_subrange['density'], color=color[num], label=labels[-num-1], marker='o')

    ax[0].set_ylabel('Pressure (MeV/fm3)')
    ax[1].set_ylabel('Mass (solar mass)')
    ax[2].set_ylabel('Density (MeV/fm3)')
    for axis in ax:
        axis.set_yscale('log')


    for axis in ax:
        axis.set_xlabel('r (km)')
        axis.legend()

        
if __name__ == '__main__':
    fig, ax = plt.subplots()
    PressureComposition(ax, 'SLy8', 'Results/Newest.csv')
    #PressureComposition('MSkA', 'Results/Newest_AACrust.csv')
    #plt.yscale('log')
    plt.show()
