import sys
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.use('Agg')
import pickle
from collections import namedtuple
from Plots.FillableHist import FillableHist2D
import numpy as np
from Utilities.Utilities import *

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams['errorbar.capsize'] =  2

plt.rcParams['font.family'] = 'serif'
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']

DataStruct = namedtuple("DataStruct", ["data", "edgecolor", "facecolor", "style", "label"])

data = {}
data['PREXII'] = DataStruct("0.625 0 2.38 0.75", "magenta", "white", "*", "PREX-II")
data['pi'] = DataStruct("1.45 0 10.9 8.7", "red", "white", "v", r"HIC($\pi$)")
data['np'] = DataStruct("1.5 0 12.1 8.8", "blue", "white", "s", "HIC(n/p flow)")


if len(sys.argv) == 3:
    with open(sys.argv[1], 'rb') as fid:
        fig = pickle.load(fid)
    
    ax = fig.axes[0]
    pdf_name = sys.argv[2]
else:
    fig, ax = plt.subplots(figsize=(11, 9))
    pdf_name = sys.argv[1]

plots = []
labels = []
for key, content in data.items():
    value = [float(text) for text in content.data.split()]
    value[0] = value[0]*0.16
    p = ax.errorbar(x=value[0], y=value[2], yerr=value[3], 
                    markerfacecolor=content.facecolor,
                    ecolor=content.edgecolor,
                    markeredgecolor=content.edgecolor,
                    marker=content.style,
                    markersize=20 if content.style != "*" else 30,
                    elinewidth=2,
                    markeredgewidth=2,
                    capsize=2,
                    capthick=2,
                    label=content.label,
                    linewidth=0)

ax.set_xlabel(r'$\rho$ (fm$^{-3}$)')
ax.set_ylabel(r'P$_{sym}$($\rho$) (MeV/fm$^2$)')
plt.xlim(1e-2, 3*0.16)
plt.ylim(1e-1, 2e2)
plt.yscale('log')
#plt.ylim(bottom=1)

plt.legend(frameon=False, fontsize=20, loc='lower right')
fig = mpl.pyplot.gcf()
fig.set_size_inches(11, 9)
plt.subplots_adjust(right=0.95)
plt.subplots_adjust(left=0.15, right=0.9, top=0.95, bottom=0.15)
plt.savefig(pdf_name)
