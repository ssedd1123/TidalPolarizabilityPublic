import os
import matplotlib as mpl
#mpl.use('Agg')
import matplotlib.colors as colors
mpl.use('Agg')
from Utilities.EOSLoader import EOSLoader
from Plots.FillableHist import FillableHist2D
from Plots.DrawSym15 import target_name, target_mean, target_sd, GausProd
from Plots.DrawAcceptedEOSSpiRIT2 import GetMeanAndBounds
import numpy as np
import pandas as pd
import sys
import matplotlib.pyplot as plt
import matplotlib.path as pltPath
import matplotlib.patches as patches
import itertools as it
import logging
import scipy
from scipy.signal import savgol_filter
from scipy import interpolate
import pickle
from copy import copy
from mpi4py import MPI
from functools import partial


from Utilities.MasterSlave import MasterSlave

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams['errorbar.capsize'] =  2

plt.rcParams['font.family'] = 'serif'
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']

logging.basicConfig(level=logging.CRITICAL)

def ContourToPatches(value, contour, **args):
    contour = [[x, y] for x, y in zip(value, contour)]
    path = pltPath.Path(contour)
    return path, patches.PathPatch(path, **args)


def GetHist(name, ranges):
    start = ranges[0]
    end = ranges[1]

    loader = EOSLoader(name, start=start, end=end)
    g = None 
    g_Post = None
    weights = GausProd(np.atleast_2d(loader.store.select('Additional_info', start=start, stop=end)[target_name].values), target_mean, target_sd)
    first = False
    if start == 0:
        first = True
    for i, weight in enumerate(weights):#range(num_load):
      #i = i + start
      if first:
         print(i, end='\r', flush=True)
      if loader.reasonable.iloc[i]:
        if np.isnan(weight) or weight == 0:
          continue

        eos = loader.GetNuclearEOS(i)
        density = np.linspace(0.16, 5*0.16, 100)
        pressure = eos.GetPressure(density, pfrac=0.5)
 
        if np.isnan(weight) or weight == 0:
          continue
        if g is None:
          g = FillableHist2D(density, pressure, bins=[100,10000], logy=False, range=[[0.16, 5*0.16], [-500, 5e3]], smooth=True, weights=[1]*density.shape[0])
          g_Post = FillableHist2D(density, pressure, bins=[100,10000], logy=False, range=[[0.16, 5*0.16], [-500, 5e3]], smooth=True, weights=[weight]*density.shape[0])
        else:
          g.Append(density, pressure, weights=[1]*density.shape[0])
          g_Post.Append(density, pressure, weights=[weight]*density.shape[0])
    loader.Close()
    return g, g_Post

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
logging.basicConfig(filename='log/app_rank%d.log' % rank, format='Process id %(process)d: %(name)s %(levelname)s - %(message)s', level=logging.DEBUG)
#logging.basicConfig(format='Process id %(process)d: %(name)s %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
  mslave = MasterSlave(comm)
  if len(sys.argv) <= 2:
    print('This script generates pdf images for rejected EOS')
    print('Input: List of filenames from deformability calculation')
    print('Output: pdf files of the image')
    print(' To use, enter\npython %s pdf_name input1 input2 ....' % sys.argv[0])
  else:
    with pd.HDFStore(sys.argv[2], 'r') as store:
        num_load = store.get_storer('kwargs').nrows
    CI = 0.95

    # first draw Ksym vs Lsym
    hist = None
    pdf_name = sys.argv[1]

    # draw example EOSs
    # draw boundary
    g = None
    g_Post = None
    ranges = []
    avail = mslave.size - 1
    batch_size = int(num_load/avail)
    start = 0
    for i in range(avail):
        ranges.append([start, start + batch_size if i != avail - 1 else num_load - 1])
        start = start + batch_size
    print(ranges)

    #for r in ranges:
    #    g, gnew = GetHist(sys.argv[2], r)
    for gnew, gnew_Post in mslave.map(partial(GetHist, sys.argv[2]), ranges, chunk_size=1):
        if g is None:
            g = gnew
            g_Post = gnew_Post
        else:
            g += gnew
            g_Post += gnew_Post

    fig, ax = plt.subplots(figsize=(11,9))
    #import matplotlib as mpl
    #g.Draw(ax)#, norm=mpl.colors.LogNorm())#, cmap=mpl.cm.gray)

    x, mean, lowerB, upperB = GetMeanAndBounds(g_Post, CI=CI)
    ax.fill_between(x, lowerB, upperB, alpha=1, color='aqua', label='%g%% C.I. with constraints' % (CI*100), zorder=0)
    #x, mean, lowerB, upperB = GetMeanAndBounds(g_Post, CI=0.68)
    #plt.plot(x, mean, label='medium', zorder=2)
    #ax.fill_between(x, lowerB, upperB, alpha=1, color='skyblue', label='68%% C.I. with constraints', zorder=1)
    x, mean, lowerB, upperB = GetMeanAndBounds(g, CI=CI)
    ax.fill_between(x, lowerB, upperB, alpha=1, edgecolor='blue', facecolor='none', linestyle='--', label='%g%% C.I. without constraints' % (CI*100), zorder=3)


    ## draw symmetric matter constraints from Kaon and flow
    ##constraints = pd.read_csv('Constraints/KaonSymMat.csv')
    ##path, patch = ContourToPatches(constraints['rho/rho0']*0.16, constraints['P(MeV/fm3)'],
    ##                               linewidth=5, edgecolor='navy', alpha=1,
    ##                               hatch='\\', lw=2, zorder=10, fill=False, label='Kaon')
    ##ax.add_patch(copy(patch))
    constraints = pd.read_csv('Constraints/FlowSymMat.csv')
    path, patch = ContourToPatches(constraints['rho/rho0']*0.16, constraints['P(MeV/fm3)'],
                                   linewidth=5, edgecolor='black', alpha=1,
                                   hatch='/', lw=2, zorder=10, fill=False, label='Flow from Au + Au.')
    ax.add_patch(copy(patch))


    plt.yscale('log')
    plt.xlabel(r'$\rho$ (fm$^{-3}$)')
    plt.ylabel(r'P$_{sym}$($\rho$) (MeV/fm$^{3}$)')
    plt.ylim(1, 1e3)
    plt.xlim(0.16, 5*0.16)
    plt.legend(loc='lower right', fontsize=20)
    plt.tight_layout()
    plt.savefig(pdf_name)
    with open(pdf_name.replace('.pdf', '.pkl'), 'wb') as fid:
        pickle.dump(fig, fid)

  mslave.Close()
