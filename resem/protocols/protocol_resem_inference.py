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

import json
import logging
logger = logging.getLogger(__name__)

from pwem.protocols import ProtAnalysis3D
import pyworkflow.utils as pwutils
from pyworkflow.protocol.params import (PointerParam, StringParam,  NonEmpty,
                                        GPU_LIST)
from pyworkflow import BETA

from resem import Plugin, PROGRAM_INFERENCE


class ProtResemInference(ProtAnalysis3D):
    """
    Wrapper protocol for the Resem's to inference.
    """
    _label = 'inference'
    _devStatus = BETA

    def _defineParams(self, form):
        form.addSection(label='Input')
        form.addParam('refVolume', PointerParam, pointerClass='Volume',
                      important=True,
                      label="Input volume",
                      help='Provide a reference volume for inference')
        form.addHidden(GPU_LIST, StringParam, default='0',
                       label='Choose GPU ID:', validators=[NonEmpty],
                       help='This argument is necessary. By default, the '
                            'protocol will attempt to launch on GPU 0. You can '
                            'override the default allocation by providing a '
                            'single GPU (0, 1, 2 or 3, etc) to use.')

        # -----------[Inference]------------------------
        form.addSection(label="Inference")
        #TODO
        # In this section the necessary parameters for inference must be defined(config json file parameters).
        # see in: https://scipion-em.github.io/docs/release-3.0.0/docs/developer/creating-a-protocol.html#parameter-definition

    # --------------------------- INSERT steps functions -----------------------

    def _insertAllSteps(self):
        self._insertFunctionStep(self.inferenceStep)
        self._insertFunctionStep(self.createOutputStep)

    # --------------------------- STEPS functions ------------------------------

    def inferenceStep(self):
        self.info(pwutils.yellowStr("Inference started..."))

        inferenceConfigFile = self.generateConfigFile()

        args = '--config  %s ' % inferenceConfigFile

        Plugin.runResEM(self, Plugin.getProgram(PROGRAM_INFERENCE),
                        args=args)

    def generateConfigFile(self):
        """
        Method to generate/modify the inference config file
        :return: the config file path
        """
        configFilePath = Plugin.getHome('configs/inference.json')
        outputConfigFile = self._getExtraPath('inference_output.json')
        try:
            # Load the JSON file
            with open(configFilePath, 'r') as file:
                data = json.load(file)

            #TODO Take all the json parameters and modify them.

            data['general']['gpu_id'] = getattr(self, GPU_LIST).get()
            data['general']['seed'] = 3

            # Updating the path for test_data
            for key, value in data['test_data'].items():
                if key.__contains__('path'):
                    data['test_data'][key] = Plugin.getHome(value)

            # Updating the path for checkpoints
            for key, value in data['checkpoint'].items():
                data['checkpoint'][key] = Plugin.getHome(value)

            # Save the file with changes
            with open(outputConfigFile, 'w') as file:
                json.dump(data, file, indent=4)

            return outputConfigFile

        except FileNotFoundError:
            logger.error(f"The file '{configFilePath}' not found")
        except Exception as e:
           logger.error("Error:", e)

    def createOutputStep(self):
        """
        Create the protocol output.
        """
        pass

    # --------------------------- INFO functions -------------------------------
    def _validate(self):
        """ Should be overwritten in subclasses to
            return summary message for NORMAL EXECUTION."""
        pass

    def _summary(self):
        return ["No summary information."]

