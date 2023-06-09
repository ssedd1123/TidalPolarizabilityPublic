from autograd import elementwise_grad as egrad
from copy import copy
import matplotlib.pyplot as plt
import matplotlib.path as pltPath
import matplotlib.patches as patches
import autograd.numpy as np
import pandas as pd

import Utilities.Utilities as utl
import Utilities.SkyrmeEOS as sky 
from Utilities.Constants import *


def ContourToPatches(value, contour, **args):
    contour = [[x, y] for x, y in zip(value, contour)]
    path = pltPath.Path(contour)
    return path, patches.PathPatch(path, **args)

if __name__ == "__main__":
    rho0 = 0.16
    constraints = pd.read_csv('Constraints/KaonSymMat.csv')
    density = np.array(constraints['rho/rho0'].tolist())
    pressure = np.array(constraints['P(MeV/fm3)'].tolist())
    def F_stiff(rho):
        return 2*rho*rho/(1+rho)#np.sqrt(rho)
    def F_soft(rho):
        return np.sqrt(rho)
    def SymEnergy(rho, F):
        fermi_ave = 22.0
        return (np.power(2,0.66666667) - 1.)*fermi_ave*(np.power(rho, 0.666666667) - F(rho)) + 30*F(rho)
    additional_constraints_fig1 = pd.read_csv('Constraints/x_1_fig1.csv')
    eos_spline = sky.EOSSpline(additional_constraints_fig1['rho/rho0']*rho0, additional_constraints_fig1['P(MeV/fm3)'], smooth=0.5)

    P_sym_soft = rho0*density*density*egrad(SymEnergy, 0)(density, F_soft)
    P_sym_stiff = rho0*density*density*egrad(SymEnergy, 0)(density, F_stiff)
    pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': P_sym_soft}).to_csv('SoftSym.csv', sep='\t', index=False)
    pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': P_sym_stiff}).to_csv('StiffSym.csv', sep='\t', index=False)
    P_sym_fig1 = eos_spline.GetPressure(density*rho0, 0)

    _, sym_patch_soft = ContourToPatches(density, pressure + 1.5*P_sym_soft, alpha=0.5, color='red', label='soft')
    _, sym_patch_stiff = ContourToPatches(density, pressure + 1.5*P_sym_stiff, alpha=0.5, color='blue', label='stiff')
    #_, sym_patch_fig1 = ContourToPatches(density, pressure + P_sym_fig1, alpha=0.5, color='blue', label='Fig1')
    pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': pressure + 1.5*P_sym_soft}).to_csv('KaonSoftUpper.csv', sep=',', index=False)
    pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': pressure + 1.5*P_sym_stiff}).to_csv('KaonStiffUpper.csv', sep=',', index=False)
    #pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': pressure + P_sym_fig1}).to_csv('KaonFig1.csv', sep=',', index=False)

    _, sym_patch_soft_min = ContourToPatches(density, pressure + 0.5*P_sym_soft, alpha=0.5, color='red', label='soft')
    _, sym_patch_stiff_min = ContourToPatches(density, pressure + 0.5*P_sym_stiff, alpha=0.5, color='blue', label='stiff')
    #_, sym_patch_fig1 = ContourToPatches(density, pressure + P_sym_fig1, alpha=0.5, color='blue', label='Fig1')
    pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': pressure + 0.5*P_sym_soft}).to_csv('KaonSoftLower.csv', sep=',', index=False)
    pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': pressure + 0.5*P_sym_stiff}).to_csv('KaonStiffLower.csv', sep=',', index=False)
    pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': P_sym_soft}).to_csv('KaonSoftAsymTerm.csv', sep=',', index=False)
    pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': P_sym_stiff}).to_csv('KaonStiffAsymTerm.csv', sep=',', index=False)

    constraints = pd.read_csv('Constraints/FlowSymMat.csv')
    density = np.array(constraints['rho/rho0'].tolist())
    pressure = np.array(constraints['P(MeV/fm3)'].tolist())

    P_sym_soft = rho0*density*density*egrad(SymEnergy, 0)(density, F_soft)
    P_sym_stiff = rho0*density*density*egrad(SymEnergy, 0)(density, F_stiff)
    _, given_patch_soft = ContourToPatches(density, pressure + 1.5*P_sym_soft, alpha=0.5, color='red', label='soft')
    _, given_patch_stiff = ContourToPatches(density, pressure + 1.5*P_sym_stiff, alpha=0.5, color='blue', label='stiff')

    _, given_patch_soft_min = ContourToPatches(density, pressure + 0.5*P_sym_soft, alpha=0.5, color='red', label='soft')
    _, given_patch_stiff_min = ContourToPatches(density, pressure + 0.5*P_sym_stiff, alpha=0.5, color='blue', label='stiff')

    pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': P_sym_soft}).to_csv('FlowSoftAsymTerm.csv', sep=',', index=False)
    pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': P_sym_stiff}).to_csv('FlowStiffAsymTerm.csv', sep=',', index=False)
    pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': pressure + 0.5*P_sym_soft}).to_csv('FlowSoftLower.csv', sep=',', index=False)
    pd.DataFrame({'rho/rho0': density, 'P(MeV/fm3)': pressure + 0.5*P_sym_stiff}).to_csv('FlowStiffLower.csv', sep=',', index=False)
    

    constraints = pd.read_csv('Constraints/FlowAsymSoft.csv')
    _, flow_patch_soft = ContourToPatches(constraints['rho/rho0'], constraints['P(MeV/fm3)'], alpha=0.5, color='orange', label='soft_original')
    constraints = pd.read_csv('Constraints/FlowAsymStiff.csv')
    _, flow_patch_stiff = ContourToPatches(constraints['rho/rho0'], constraints['P(MeV/fm3)'], alpha=0.5, color='orange', label='stiff_original')


    ax = plt.subplot(111)
    ax.add_patch(sym_patch_soft)
    ax.add_patch(sym_patch_stiff)
    ax.add_patch(sym_patch_soft_min)
    ax.add_patch(sym_patch_stiff_min)
    ax.add_patch(given_patch_soft)
    ax.add_patch(given_patch_stiff)
    ax.add_patch(flow_patch_soft)
    ax.add_patch(flow_patch_stiff)
    ax.add_patch(given_patch_soft_min)
    ax.add_patch(given_patch_stiff_min)
    #ax.add_patch(sym_patch_fig1)
    ax.plot([1,5], [1, 400])
    ax.set_yscale('log')
    ax.legend()
    plt.show()
