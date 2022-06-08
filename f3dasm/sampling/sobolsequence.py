import numpy as np
from SALib.sample import sobol_sequence

from ..src.samplingmethod import SamplingMethod


class SobolSequencing(SamplingMethod):
    """Sampling via Sobol Sequencing with SALib"""
    def sample(self, numsamples: int, dimensions: int) -> np.array:
        samples = sobol_sequence.sample(numsamples, dimensions)
        return samples
