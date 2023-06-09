from copy import copy
from scipy.interpolate import InterpolatedUnivariateSpline
import matplotlib.pyplot as plt
import matplotlib.path as pltPath
import matplotlib.patches as patches
import autograd.numpy as np
import pandas as pd

import Utilities.Utilities as utl
import Utilities.SkyrmeEOS as sky 
from Utilities.Constants import *

def NumTrueAbovePercentage(list_, percentage):
    num_elements = float(len(list_))
    if float(np.count_nonzero(list_)/num_elements) > percentage:
        return True
    return False 

def ContourToPatches(value, contour, **args):
    contour = [[x, y] for x, y in zip(value, contour)]
    path = pltPath.Path(contour)
    return path, patches.PathPatch(path, **args)

def SelectFlow(constraint_filename, df, accept_percentage=0.8, xmin=2, xmax=4.5, **args):
    constraints = pd.read_csv(constraint_filename)
    path, patch = ContourToPatches(constraints['rho/rho0'], constraints['P(MeV/fm3)'], **args)

    inside_list = []
    n = np.linspace(xmin, xmax, 1000)
    for index, row in df.iterrows():
        eos = sky.Skryme(row)
        pressure = eos.GetAutoGradPressure(n*rho0, 0)
        inside = path.contains_points(np.array([n, pressure]).T)
        if NumTrueAbovePercentage(inside, accept_percentage):
            inside_list.append(index)
    df_selected = df.ix[inside_list]

    return df_selected, patch

if __name__ == "__main__":
    df = pd.read_csv('Results/Skyrme_pd_0.7.csv', index_col=0)
    df.fillna(0, inplace=True)

    
    # load the constraints from flow experiments
    _, patch_soft = SelectFlow('Constraints/FlowAsymSoft.csv', df, 0.8,
                                     linewidth=5, edgecolor='navy', alpha=1,
                                     hatch='', lw=2, zorder=10, fill=False, label='Exp.+soft')
    # create cut fo stiff asym
    _, patch_stiff = SelectFlow('Constraints/FlowAsymStiff.csv', df, 0.8,
                                       linewidth=5, edgecolor='fuchsia', alpha=1,
                                       hatch='', lw=2, zorder=10, fill=False, label='Exp.+stiff')
    # load the constraints from Kaon experiments
    df_soft, patch_soft_kaon = SelectFlow('Constraints/KaonSoft.csv', df, 0.8, xmin=1.2, xmax=2.2,
                                     linewidth=5, edgecolor='black', alpha=1,
                                     hatch='', lw=2, zorder=10, fill=False, label='Kaon+soft')
    # create cut fo stiff asym
    df_stiff, patch_stiff_kaon = SelectFlow('Constraints/KaonStiff.csv', df, 0.8, xmin=1.2, xmax=2.2,
                                       linewidth=5, edgecolor='red', alpha=1,
                                       hatch='', lw=2, zorder=10, fill=False, label='Kaon+stiff')

    for index, row in df_soft.iterrows():
        eos = sky.Skryme(row)
        eos.ToCSV('AllSkyrmes/AsymSoft/%s.csv' % index, np.linspace(1e-14, 3*0.16, 100), 0)

    for index, row in df_stiff.iterrows():
        eos = sky.Skryme(row)
        eos.ToCSV('AllSkyrmes/AsymStiff/%s.csv' % index, np.linspace(1e-14, 3*0.16, 100), 0)

    # write result to file
    #df_soft.to_csv('SkyrmeParameters/SkyrmeConstraintedWithFlowSoft.csv', sep=',')
    #df_stiff.to_csv('SkyrmeParameters/SkyrmeConstraintedWithFlowStiff.csv', sep=',')

    ax1, ax2 = utl.PlotMaster(df, [df_stiff, df_soft], ['Kaon+stiff', 'Kaon+soft'], ('pink', 'royalblue'))

    #additional_constraints_fig1 = pd.read_csv('Constraints/x_1_fig1.csv')
    #spl = InterpolatedUnivariateSpline(additional_constraints_fig1['rho/rho0'], additional_constraints_fig1['P(MeV/fm3)'])
    #density = np.linspace(0, 3, 1000)
    #ax1.plot(density, spl(density), color='r', label='Xiao paper x=1', markevery=100)
    leg = ax1.legend()
    for line, text in zip(leg.get_lines(), leg.get_texts()):
        text.set_color(line.get_color())

    
    # plot the region and the legend
    ax2.add_patch(copy(patch_soft))
    ax2.add_patch(copy(patch_stiff))
    ax2.add_patch(copy(patch_soft_kaon))
    ax2.add_patch(copy(patch_stiff_kaon))
    leg = ax2.legend(loc='lower right')

    for line, text in zip(leg.get_lines(), leg.get_texts()):
        text.set_color(line.get_color())
    plt.show()
