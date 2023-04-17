#                                                                       Modules
# =============================================================================

# Standard
import json
from dataclasses import dataclass, field
from typing import Any, List, Type

# Third-party core
import numpy as np

#                                                          Authorship & Credits
# =============================================================================
__author__ = 'Martin van der Schelling (M.P.vanderSchelling@tudelft.nl)'
__credits__ = ['Martin van der Schelling']
__status__ = 'Stable'
# =============================================================================
#
# =============================================================================


@dataclass
class Parameter:
    """Interface class of a search space parameter

    Parameters
    ----------
    name
        name of the parameter
    """

    name: str
    _type: str = field(init=False, default="object")

    @classmethod
    def from_json(cls: Type['Parameter'], json_string: str) -> 'Parameter':
        """
        Create a Parameter object from a JSON string.

        Parameters
        ----------
        json_string : str
            JSON string representation of the information to construct the Parameter.

        Returns
        -------
        Parameter
            The requested Parameter object.
        """
        parameter_dict, name = json.loads(json_string)
        return cls.from_dict(parameter_dict, name)

    @classmethod
    def from_dict(cls: Type['Parameter'], parameter_dict: dict, name: str) -> 'Parameter':
        """
        Create a Parameter object from a dictionary.

        Parameters
        ----------
        parameter_dict : dict
            Dictionary representation of the information to construct the Parameter.
        name : str
            Name of the class.

        Returns
        -------
        Parameter
            The requested Parameter object.
        """
        if name == 'Parameter':
            return cls(**parameter_dict)
        else:
            return _find_parameter(name)(**parameter_dict)

    @classmethod
    def get_name(self) -> str:
        """Return the name of the parameter class"""
        return self.__name__

    def to_json(self) -> str:
        """Return a JSON string representation of the parameter"""
        args = self.__dict__
        name = self.get_name()
        return json.dumps((args, name))


@dataclass
class ConstantParameter(Parameter):
    """Create a search space parameter that is constant.

    Parameters
    ----------
    name : str
        The name of the parameter.
    value : Any
        The constant value of the parameter.

    Attributes
    ----------
    _type : str
        The type of the parameter, which is always 'object'.

    Raises
    ------
    TypeError
        If the value is not hashable.

    """

    value: Any
    _type: str = field(init=False, default="object")

    def __post_init__(self):
        self._check_hashable()

    def _check_hashable(self):
        """Check if the value is hashable."""
        try:
            hash(self.value)
        except TypeError:
            raise TypeError("The value must be hashable.")


@dataclass
class ContinuousParameter(Parameter):
    """
    A search space parameter that is continuous.

    Attributes
    ----------
    name : str
        The name of the parameter.
    lower_bound : float, optional
        The lower bound of the continuous search space. Defaults to negative infinity.
    upper_bound : float, optional
        The upper bound of the continuous search space (exclusive). Defaults to infinity.

    Raises
    ------
    TypeError
        If the boundaries are not floats.
    ValueError
        If the upper bound is less than the lower bound, or if the lower bound is equal to the upper bound.

    Notes
    -----
    This class inherits from the `Parameter` class and adds the ability to specify a continuous search space.
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
            raise TypeError(
                f"Expect float, got {type(self.lower_bound)} and {type(self.upper_bound)}")

    def _check_range(self):
        """Check if the lower boundary is lower than the higher boundary"""
        if self.upper_bound < self.lower_bound:
            raise ValueError("not the right range!")

        if self.upper_bound == self.lower_bound:
            raise ValueError("same lower as upper bound!")


@dataclass
class DiscreteParameter(Parameter):
    """Create a search space parameter that is discrete

    Parameters
    ----------
    name
        name of the parameter
    lower_bound
        lower bound of discrete search space
    upper_bound
        upper bound of discrete search space (exclusive)
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
            raise TypeError(
                f"Expect integer, got {type(self.lower_bound)} and {type(self.upper_bound)}")

    def _check_range(self):
        """Check if the lower boundary is lower than the higher boundary"""
        if self.upper_bound < self.lower_bound:
            raise ValueError("not the right range!")

        if self.upper_bound == self.lower_bound:
            raise ValueError("same lower as upper bound!")


@dataclass
class CategoricalParameter(Parameter):
    """Create a search space parameter that is categorical

    Parameters
    ----------
    name
        name of the parameter
    categories
        list of strings that represent available categories
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

        self.categories = list(self.categories)  # Convert to list because hydra parses omegaconf.ListConfig

        if not isinstance(self.categories, list):
            raise TypeError(f"Expect list, got {type(self.categories)}")

        for category in self.categories:
            if not isinstance(category, str):
                raise TypeError(f"Expect string, got {type(category)}")


PARAMETERS = [CategoricalParameter, ConstantParameter, ContinuousParameter, DiscreteParameter]


class F3DASMParameterNotFoundError(Exception):
    """
    Exception raised when a parameter is not found.

    Attributes:
        message (str): The error message.
    """

    def __init__(self, message):
        super().__init__(message)


def _find_parameter(query: str) -> Parameter:
    """
    Find a Parameter class by its name.

    Parameters
    ----------
    query : str
        The name of the requested Parameter class.

    Returns
    -------
    Parameter
        The class object of the requested Parameter.

    Raises
    ------
    F3DASMParameterNotFoundError
        If the requested parameter is not found.
    """
    try:
        return list(filter(lambda parameter: parameter.__name__ == query, PARAMETERS))[0]
    except IndexError:
        return F3DASMParameterNotFoundError(f'Parameter {query} not found!')
