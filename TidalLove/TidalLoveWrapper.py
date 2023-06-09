import tempfile
import TidalLove.TidalLove_individual as tidal
from decimal import Decimal
import autograd.numpy as np
import scipy.optimize as opt
import math
import logging
from copy import copy
from multiprocessing_logging import install_mp_handler

logger = logging.getLogger(__name__)
install_mp_handler(logger)

import Utilities.Utilities as utl
import Utilities.SkyrmeEOS as sky 
from Utilities.Constants import *

class TidalLoveResult:

    def __init__(self, num_checkpoints=0):
        self.mass = np.nan
        self.PCentral = np.nan
        self.DensCentral = np.nan
        self.Radius = np.nan
        self.Lambda = np.nan
        self.Checkpoint_mass = [np.nan]*num_checkpoints
        self.Checkpoint_radius = [np.nan]*num_checkpoints
        self.Checkpoint_dens = [np.nan]*num_checkpoints

    def ToDict(self):
        dictionary = {'Mass' : self.mass,
                      'PCentral' : self.PCentral,
                      'DensCentral' : self.DensCentral,
                      'R' : self.Radius,
                      'Lambda' : self.Lambda}
        for index, (cp_mass, cp_radius, cp_dens) in enumerate(zip(self.Checkpoint_mass, self.Checkpoint_radius, self.Checkpoint_dens)):
            dictionary['RadiusCheckpoint%d' % index] = cp_radius
            dictionary['MassCheckpoint%d' % index] = cp_mass
            dictionary['DensityCheckpoint%d' % index] = cp_dens
        return dictionary

    def IsNan(self):
        return np.isnan(self.mass)

   
class TidalLoveWrapper:


    def __init__(self, eos, name=None):
        """
        Print the selected EOS into a file for the tidallove script to run
        """
        self.eos = eos
        if name is None:
            logger.debug('Write EOS into temp file')
            self.output = tempfile.NamedTemporaryFile('w')
        else:
            logger.debug('Write EOS into file %s' % name)
            self.output = open(name, 'w')
        eos.ToFileStream(self.output)
        self.max_energy, self.max_pressure = eos.GetMaxDef()
        logger.debug('EOS is valid up till energy = %f, pressure = %f' % (self.max_energy, self.max_pressure))
        # pressure needs to be expressed as pascal for pc
        #self.max_pressure# /= 3.62704e-5
        self.ans = TidalLoveResult()
        self.surface_pressure = 1e-8 # default pressure defined at surface
        self._checkpoint = [self.surface_pressure]
        self._named_density_checkpoint = []
        self._density_checkpoint = []

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.Close()

    @property
    def checkpoint(self):
        return self._checkpoint

    @checkpoint.setter
    def checkpoint(self, value):
        # checkpoint list must be in desending order
        value.sort(reverse=True)
        self._density_checkpoint = []
        for pre in value:
            try:
                self._density_checkpoint.append(opt.newton(lambda rho: self.eos.GetPressure(rho, 0) - pre, x0=self.eos.rho0, 
                                                           fprime=lambda x: self.eos.GetdPressure(x, 0)))
            except Exception:
                self._density_checkpoint.append(0)
        self._checkpoint = value

    @property
    def density_checkpoint(self):
        return self._density_checkpoint

    @density_checkpoint.setter
    def density_checkpoint(self, value):
        value.sort(reverse=True)
        self._checkpoint = self.eos.GetPressure(np.array(value), 0).tolist()
        self._density_checkpoint = value

    @property
    def named_density_checkpoint(self):
        return self._named_density_checkpoint
 
    @named_density_checkpoint.setter
    def named_density_checkpoint(self, value):
        # named checkpoints must be list of tuple
        value.sort(reverse=True, key=lambda tup: tup[1])
        self._named_density_checkpoint = value
        self.density_checkpoint = [val[1] for val in value]


    def Calculate(self, pc):
        # return order
        # m r lambda_ checkpt_m checkpt_r
        self.ans = TidalLoveResult(len(self.density_checkpoint))
        ans = tidal.tidallove_individual(self.output.name, 
                                         pc, self.max_energy, self.surface_pressure, np.array(self.checkpoint), )
        #if(len(ans[4]) > 0):
        if ans[0] > 0:
            self.ans.mass = ans[0]
            self.ans.Radius = ans[1] 
            self.ans.Lambda = ans[2]
            self.ans.Checkpoint_mass = ans[3]
            self.ans.Checkpoint_radius = ans[4]
        else:
            raise RuntimeError('Calculated mass smaller than zero. EOS exceed its valid range at pc = %f, maxp = %f' % (pc, self.max_pressure))

        return self.ans

    def FindMaxMass(self, central_pressure0=10, disp=False, *args):
        if central_pressure0 > self.max_pressure:
            logger.warning('Default pressure %g exceed max. valid pressure %.3f. Will ignore default pressure' % (central_pressure0, self.max_pressure))
            central_pressure0 = 0.7*self.max_pressure
        # try finding the maximum mass
        pc = np.nan
        while central_pressure0 < self.max_pressure:
            try:
                pc = opt.minimize(lambda x: -1e6*self.Calculate(float(x)).mass, 
                                  x0=np.array([central_pressure0]), 
                                  bounds=((0.01, 0.95*self.max_pressure),), 
                                  options={'eps':0.1, 'ftol':1e-3})
                pc = pc['x'][0]
            except Exception as error:
                central_pressure0 = central_pressure0*2
                logger.exception('Failed to find max mass with central_pressure %f' % central_pressure0)
            else:
                break
        # infer central density from central pressure
        try:
            DensCentralMax = opt.newton(lambda x: self.eos.GetPressure(x, 0) - pc, x0=5*0.16,
                                        fprime=lambda x: self.eos.GetdPressure(x, 0)) 
        except Exception as error:
            logger.exception('Cannot find central density for mass %g' % self.ans['mass'])
            DensCentralMax = np.nan

        self.ans.PCentral = pc
        self.ans.DensCentral = DensCentralMax
        return copy(self.ans)

    def FindMass(self, central_pressure0=10, mass=1.4, *args, **kwargs):
        if central_pressure0 > self.max_pressure:
            logger.warning('Default pressure %g exceed max. valid pressure %.3f. Will ignore default pressure' % (central_pressure0, self.max_pressure))
            central_pressure0 = 0.7*self.max_pressure
        try:
            pc = opt.newton(lambda x: self.Calculate(x).mass - mass, 
                            x0=central_pressure0, *args, **kwargs)
        except Exception as error:
            logger.exception('Failed to find NS mass %g' % mass)
            pc = np.nan

        try:
            DensCentral = opt.newton(lambda x: self.eos.GetPressure(x, 0) - pc, x0=1.5*0.16,
                                     fprime=lambda x: self.eos.GetdPressure(x, 0)) 
        except Exception as error:
            logger.exception('Cannot find central density for mass %g' % mass)
            DensCentral = np.nan

        self.ans.PCentral = pc
        self.ans.DensCentral = DensCentral
        return copy(self.ans)

    def Close(self):
        self.output.close()
    
