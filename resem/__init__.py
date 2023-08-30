# **************************************************************************
# *
# * Authors: Yunior C. Fonseca Reyna    (cfonseca@cnb.csic.es)
# *
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************


import os

import pwem
import pyworkflow.utils as pwutils

from .constants import *

__version__ = "3.0.0"
_logo = "icon.png"
_references = ['CryoFEM2023']


class Plugin(pwem.Plugin):
    _homeVar = RESEM_HOME
    _pathVars = [RESEM_HOME]

    @classmethod
    def _defineVariables(cls):
        cls._defineVar(RESEM_CUDA_LIB, pwem.Config.CUDA_LIB)
        cls._defineEmVar(RESEM_HOME, 'resem-' + RESEM_VERSION)

    @classmethod
    def getEnviron(cls):
        """ Set up the environment variables needed to launch ResEM. """
        environ = pwutils.Environ(os.environ)
        # Add required disperse path to PATH and python path to PYTHONPATH
        environ.update({'PATH': os.path.join(cls.getHome()),
                        'PYTHONPATH':  cls.getHome()
                        }, position=pwutils.Environ.END)
        cudaLib = cls.getVar(RESEM_CUDA_LIB)
        environ.addLibrary(cudaLib)
        return environ

    @classmethod
    def getResEMActivationCmd(cls):
        return RESEM_ACTIVATION_CMD

    @classmethod
    def getHome(cls, *paths):
        home = cls.getVar(cls._homeVar)
        return os.path.join(home, 'ResEM', *paths) if home else ''


    @classmethod
    def getDependencies(cls):
        """ Return a list of dependencies. Include conda if
            activation command was not found. """
        condaActivationCmd = cls.getCondaActivationCmd()
        neededProgs = ['wget', 'tar', 'unzip']
        if not condaActivationCmd:
            neededProgs.append('conda')

        return neededProgs

    @classmethod
    def runResEM(cls, protocol, program, args, cwd=None, useCpu=False):
        """ Run ResEM command from a given protocol. """
        fullProgram = '%s %s && python %s' % (cls.getCondaActivationCmd(),
                                       cls.getResEMActivationCmd(),
                                       program)

        protocol.runJob(fullProgram, args, env=cls.getEnviron(), cwd=cwd,
                        numberOfMpi=1)

    @classmethod
    def getProgram(cls, program):
        programPath = os.path.join(cls.getHome(),  program)
        return programPath

    @classmethod
    def addResEMPackage(cls, env):
        RESEM_INSTALLED = f"resem_{RESEM_VERSION}_installed"
        ENV_NAME = getResEMEnvName(RESEM_VERSION)
        torchioVersion = 'torchio==0.18.86'
        pythonVersion = 'python=3.9'
        numpyVersion = 'numpy==1.24.1'
        mrcfileVersion = 'mrcfile==1.4.3'
        scikitVersion = 'scikit-image==0.19.3'
        tqdmVersion = 'tqdm==4.64.1'
        torchvision = 'torchvision==0.15.2'
        ml_collections = 'ml_collections==0.1.1'

        installCmd = [cls.getCondaActivationCmd(),
                      f'conda create -y -n {ENV_NAME} {pythonVersion} -c conda-forge -c anaconda && ',
                      f'conda activate {ENV_NAME} &&']
        installCmd.append(f'conda install -y scipy pyqt &&')
        installCmd.append(f'pip install {torchioVersion} {scikitVersion} {mrcfileVersion} {numpyVersion} {tqdmVersion} {torchvision} '
                          f'{ml_collections} &&')
        # download ResEM
        resemFolderName = 'CryoFEM-main'
        installCmd.append(f'wget https://github.com/Structurebiology-BNL/CryoFEM/archive/refs/heads/master.zip && unzip master.zip  && ')
        installCmd.append(f'mv {resemFolderName} ResEM && ')
        installCmd.append(f'touch {RESEM_INSTALLED}')

        pyem_commands = [(" ".join(installCmd), [RESEM_INSTALLED])]

        envPath = os.environ.get('PATH', "")
        installEnvVars = {'PATH': envPath} if envPath else None
        env.addPackage('resem', version=RESEM_VERSION,
                       tar='void.tgz',
                       commands=pyem_commands,
                       neededProgs=cls.getDependencies(),
                       default=True,
                       vars=installEnvVars)

    @classmethod
    def defineBinaries(cls, env):
        cls.addResEMPackage(env)
