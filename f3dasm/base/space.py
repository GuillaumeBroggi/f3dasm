from dataclasses import dataclass, field
from typing import List

import autograd.numpy as np


@dataclass
class ParameterInterface:
    """Interface class of a search space parameter

    :param name: name of the parameter
    """

    name: str
    _type: str = field(init=False)


@dataclass
class ContinuousParameter(ParameterInterface):
    """Creates a search space parameter that is continuous

    :param name: name of the parameter
    :param lower_bound: lower bound of continuous search space
    :param upper_bound: upper bound of continuous search space (exclusive)
    """

    lower_bound: float = field(default=-np.inf)
    upper_bound: float = field(default=np.inf)
    _type: str = field(init=False, default="float")

    def __post_init__(self):
        self._check_types()
        self._check_range()

    def _check_types(self):
        """Check if the boundaries are actually floats"""
        if not isinstance(self.lower_bound, float) or not isinstance(self.upper_bound, float):
            raise TypeError(f"Expect float, got {type(self.lower_bound)} and {type(self.upper_bound)}")

    def _check_range(self):
        """Check if the lower boundary is lower than the higher boundary"""
        if self.upper_bound < self.lower_bound:
            raise ValueError("not the right range!")

        if self.upper_bound == self.lower_bound:
            raise ValueError("same lower as upper bound!")


@dataclass
class DiscreteParameter(ParameterInterface):
    """Creates a search space parameter that is discrete

    :param lower_bound: lower bound of discrete search space
    :param upper_bound: upper bound of discrete search space (exclusive)
    :param name: name of the parameter
    """

    lower_bound: int = field(default=0)
    upper_bound: int = field(default=1)
    _type: str = field(init=False, default="int")

    def __post_init__(self):
        self._check_types()
        self._check_range()

    def _check_types(self):
        """Check if the boundaries are actually ints"""
        if not isinstance(self.lower_bound, int) or not isinstance(self.upper_bound, int):
            raise TypeError(f"Expect integer, got {type(self.lower_bound)} and {type(self.upper_bound)}")

    def _check_range(self):
        """Check if the lower boundary is lower than the higher boundary"""
        if self.upper_bound < self.lower_bound:
            raise ValueError("not the right range!")

        if self.upper_bound == self.lower_bound:
            raise ValueError("same lower as upper bound!")


@dataclass
class CategoricalParameter(ParameterInterface):
    """Creates a search space parameter that is categorical

    :param categories: list of strings that represent available categories
    :param name: name of the parameter
    """

    categories: List[str]
    _type: str = field(init=False, default="category")

    def __post_init__(self):
        self._check_types()
        self._check_duplicates()

    def _check_duplicates(self):
        """Check if there are duplicates in the categories list"""
        if len(self.categories) != len(set(self.categories)):
            raise ValueError("Categories contain duplicates!")

    def _check_types(self):
        """Check if the entries of the lists are all strings"""

        if not isinstance(self.categories, list):
            raise TypeError(f"Expect list, got {type(self.categories)}")

        for category in self.categories:
            if not isinstance(category, str):
                raise TypeError(f"Expect string, got {type(category)}")


@dataclass
class ConstraintInterface:
    """Interface for constraints"""

    pass
