"""
The Domain is a set of Parameter instances that make up the feasible search space.
"""

#                                                                       Modules
# =============================================================================

from __future__ import annotations

# Standard
import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple, Type, TypeVar

# Third-party core
import numpy as np
import pandas as pd
from hydra.utils import instantiate
from omegaconf import DictConfig

# Local
from .parameter import (CategoricalParameter, ConstantParameter,
                        ContinuousParameter, DiscreteParameter, Parameter)

#                                                          Authorship & Credits
# =============================================================================
__author__ = 'Martin van der Schelling (M.P.vanderSchelling@tudelft.nl)'
__credits__ = ['Martin van der Schelling']
__status__ = 'Stable'
# =============================================================================
#
# =============================================================================


@dataclass
class Domain:
    """Main class for defining the domain of the design of experiments.

    Parameters
    ----------
    input_space : Dict[str, Parameter], optional
        Dict of input parameters, by default an empty dict
    """

    input_space: Dict[str, Parameter] = field(default_factory=dict)

    def __len__(self) -> int:
        """The len() method returns the number of parameters"""
        return len(self.input_space)

    def __eq__(self, other: Domain) -> bool:
        """Custom equality comparison for Domain objects."""
        if not isinstance(other, Domain):
            return False

        # Compare the input_space dictionaries for equality
        return self.input_space == other.input_space

    @property
    def names(self) -> List[str]:
        """Return a list of the names of the parameters"""
        return list(self.input_space.keys())

#                                                      Alternative constructors
# =============================================================================

    @classmethod
    def from_file(cls: Type[Domain], filename: Path) -> Domain:
        """Create a Domain object from a pickle file.

        Parameters
        ----------
        filename : Path
            Name of the file.

        Returns
        -------
        Domain
            Domain object containing the loaded data.
        """

        # Check if filename exists
        if not filename.with_suffix('.pkl').exists():
            raise FileNotFoundError(f"Domain file {filename} does not exist.")

        with open(filename.with_suffix('.pkl'), "rb") as file:
            obj = pickle.load(file)

        return obj

    @classmethod
    def from_yaml(cls: Type[Domain], yaml: DictConfig) -> Domain:
        """Initializ a Domain from a Hydra YAML configuration file


        Notes
        -----
        The YAML file should have the following structure:
        A nested dictionary where the dictionary denote the input_space


        Parameters
        ----------
        yaml : DictConfig
            yaml dictionary

        Returns
        -------
        Domain
            Domain object
        """
        args = {}
        for space, params in yaml.items():
            args[space] = {name: instantiate(param, _convert_="all") for name, param in params.items()}
        return cls(**args)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> Domain:
        """Initializes a Domain from a pandas DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the input parameters.

        Returns
        -------
        Domain
            Domain object
        """
        input_space = {}
        for name, type in df.dtypes.items():
            if type == 'float64':
                input_space[name] = ContinuousParameter(lower_bound=float(
                    df[name].min()), upper_bound=float(df[name].max()))
            elif type == 'int64':
                input_space[name] = DiscreteParameter(lower_bound=int(df[name].min()), upper_bound=int(df[name].max()))
            else:
                input_space[name] = CategoricalParameter(df[name].unique().tolist())

        return cls(input_space=input_space)

#                                                                        Export
# =============================================================================

    def store(self, filename: Path) -> None:
        """Stores the Domain in a pickle file.

        Parameters
        ----------
        filename : str
            Name of the file.
        """
        with open(filename.with_suffix('.pkl'), 'wb') as f:
            pickle.dump(self, f)

    def _cast_types_dataframe(self) -> dict:
        """Make a dictionary that provides the datatype of each parameter"""
        return {name: parameter._type for name, parameter in self.input_space.items()}

    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Create an empty DataFrame with input columns.

        Returns
        -------
        pd.DataFrame
            DataFrame containing "input" columns.
        """
        # input columns
        input_columns = [name for name in self.input_space.keys()]

        return pd.DataFrame(columns=input_columns).astype(
            self._cast_types_dataframe()
        )

#                                                  Append and remove parameters
# =============================================================================

    def add(self, name: str, space: Parameter):
        """Add a new input parameter to the domain.

        Parameters
        ----------
        name : str
            Name of the input parameter.
        space : Parameter
            Input parameter to be added.

        Example
        -------
        >>> domain = Domain()
        >>> domain.add_input_space('param1', ContinuousParameter(lower_bound=0., upper_bound=1.))
        >>> domain.input_space
        {'param1': ContinuousParameter(lower_bound=0., upper_bound=1.)}
        """
        self.input_space[name] = space

#                                                                       Getters
# =============================================================================

    def get_continuous_parameters(self) -> Dict[str, ContinuousParameter]:
        """Get all continuous input parameters.

        Returns
        -------
        Dict[str, ContinuousParameter]
            Space of continuous input parameters.

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': ContinuousParameter(lower_bound=0., upper_bound=1.),
        ...     'param2': CategoricalParameter(categories=['A', 'B', 'C']),
        ...     'param3': ContinuousParameter(lower_bound=2., upper_bound=5.)
        ... }
        >>> continuous_input_params = domain.get_continuous_input_parameters()
        >>> continuous_input_params
        {'param1': ContinuousParameter(lower_bound=0., upper_bound=1.),
         'param3': ContinuousParameter(lower_bound=2., upper_bound=5.)}
        """
        return self.filter(ContinuousParameter).input_space

    def get_continuous_names(self) -> List[str]:
        """Get the names of continuous input parameters in the input space.

        Returns
        -------
        List[str]
            List of names of continuous input parameters.

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': ContinuousParameter(lower_bound=0., upper_bound=1.),
        ...     'param2': DiscreteParameter(lower_bound=1, upper_bound=3),
        ...     'param3': ContinuousParameter(lower_bound=2., upper_bound=5.)
        ... }
        >>> continuous_input_names = domain.get_continuous_input_names()
        >>> continuous_input_names
        ['param1', 'param3']
        """
        return self.filter(ContinuousParameter).names

    def get_discrete_parameters(self) -> Dict[str, DiscreteParameter]:
        """Retrieve all discrete input parameters.

        Returns
        -------
        Dict[str, DiscreteParameter]
            Space of discrete input parameters.

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': DiscreteParameter(lower_bound=1, upperBound=4),
        ...     'param2': CategoricalParameter(categories=['A', 'B', 'C']),
        ...     'param3': DiscreteParameter(lower_bound=4, upperBound=6)
        ... }
        >>> discrete_input_params = domain.get_discrete_input_parameters()
        >>> discrete_input_params
        {'param1': DiscreteParameter(lower_bound=1, upperBound=4)),
         'param3': DiscreteParameter(lower_bound=4, upperBound=6)}
        """
        return self.filter(DiscreteParameter).input_space

    def get_discrete_names(self) -> List[str]:
        """Retrieve the names of all discrete input parameters.

        Returns
        -------
        List[str]
            List of names of discrete input parameters.

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': DiscreteParameter(lower_bound=1, upperBound=4),
        ...     'param2': ContinuousParameter(lower_bound=0, upper_bound=1),
        ...     'param3': DiscreteParameter(lower_bound=4, upperBound=6)
        ... }
        >>> discrete_input_names = domain.get_discrete_input_names()
        >>> discrete_input_names
        ['param1', 'param3']
        """
        return self.filter(DiscreteParameter).names

    def get_categorical_parameters(self) -> Dict[str, CategoricalParameter]:
        """Retrieve all categorical input parameters.

        Returns
        -------
        Dict[str, CategoricalParameter]
            Space of categorical input parameters.

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': CategoricalParameter(categories=['A', 'B', 'C']),
        ...     'param2': ContinuousParameter(lower_bound=0, upper_bound=1),
        ...     'param3': CategoricalParameter(categories=['X', 'Y', 'Z'])
        ... }
        >>> categorical_input_params = domain.get_categorical_input_parameters()
        >>> categorical_input_params
        {'param1': CategoricalParameter(categories=['A', 'B', 'C']),
         'param3': CategoricalParameter(categories=['X', 'Y', 'Z'])}
        """
        return self.filter(CategoricalParameter).input_space

    def get_categorical_names(self) -> List[str]:
        """Retrieve the names of categorical input parameters.

        Returns
        -------
        List[str]
            List of names of categorical input parameters.

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': CategoricalParameter(categories=['A', 'B', 'C']),
        ...     'param2': ContinuousParameter(lower_bound=0, upper_bound=1),
        ...     'param3': CategoricalParameter(categories=['X', 'Y', 'Z'])
        ... }
        >>> categorical_input_names = domain.get_categorical_input_names()
        >>> categorical_input_names
        ['param1', 'param3']
        """
        return self.filter(CategoricalParameter).names

    def get_constant_parameters(self) -> Dict[str, ConstantParameter]:
        """Retrieve all constant input parameters.

        Returns
        -------
        Dict[str, ConstantParameter]
            Space of constant input parameters.

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': ConstantParameter(value=0),
        ...     'param2': CategoricalParameter(categories=['A', 'B', 'C']),
        ...     'param3': ConstantParameter(value=1)
        ... }
        >>> constant_input_params = domain.get_constant_input_parameters()
        >>> constant_input_params
        {'param1': ConstantParameter(value=0), 'param3': ConstantParameter(value=1)}
        """
        return self.filter(ConstantParameter).input_space

    def get_constant_names(self) -> List[str]:
        """Receive the names of the constant input parameters

        Returns
        -------
            list of names of constant input parameters

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': ConstantParameter(value=0),
        ...     'param2': ConstantParameter(value=1),
        ...     'param3': ContinuousParameter(lower_bound=0, upper_bound=1)
        ... }
        >>> constant_input_names = domain.get_constant_input_names()
        >>> constant_input_names
        ['param1', 'param2']
        """
        return self.filter(ConstantParameter).names

    def get_bounds(self) -> np.ndarray:
        """Return the boundary constraints of the continuous input parameters

        Returns
        -------
            numpy array with lower and upper bound for each continuous inpu dimension

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': ContinuousParameter(lower_bound=0, upper_bound=1),
        ...     'param2': ContinuousParameter(lower_bound=-1, upper_bound=1),
        ...     'param3': ContinuousParameter(lower_bound=0, upper_bound=10)
        ... }
        >>> bounds = domain.get_bounds()
        >>> bounds
        array([[ 0.,  1.],
            [-1.,  1.],
            [ 0., 10.]])
        """
        return np.array(
            [[parameter.lower_bound, parameter.upper_bound]
                for _, parameter in self.get_continuous_parameters().items()]
        )

    def filter(self, type: Type[Parameter]) -> Domain:
        """Filter the parameters of the domain by type

        Parameters
        ----------
        type : Type[Parameter]
            Type of the parameters to be filtered

        Returns
        -------
        Domain
            Domain with the filtered parameters

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': ContinuousParameter(lower_bound=0., upper_bound=1.),
        ...     'param2': DiscreteParameter(lower_bound=0, upper_bound=8),
        ...     'param3': CategoricalParameter(categories=['cat1', 'cat2'])
        ... }
        >>> filtered_domain = domain.filter_parameters(ContinuousParameter)
        >>> filtered_domain.input_space
        {'param1': ContinuousParameter(lower_bound=0, upper_bound=1)}

        """
        return Domain(
            input_space={name: parameter for name, parameter in self.input_space.items()
                         if isinstance(parameter, type)}
        )

#                                                                 Miscellaneous
# =============================================================================

    def _all_input_continuous(self) -> bool:
        """Check if all input parameters are continuous"""
        return len(self) == len(self.filter(ContinuousParameter))


def make_nd_continuous_domain(bounds: np.ndarray, dimensionality: int) -> Domain:
    """Create a continuous domain.

    Parameters
    ----------
    bounds : numpy.ndarray
        A 2D numpy array of shape (dimensionality, 2) specifying the lower and upper bounds of every dimension.
    dimensionality : int
        The number of dimensions.

    Returns
    -------
    Domain
        A continuous domain with a continuous input.

    Notes
    -----
    This function creates a Domain object consisting of continuous input parameters.
    The lower and upper bounds of each input dimension are specified in the `bounds` parameter.
    The input parameters are named "x0", "x1" ..

    Example
    -------
    >>> bounds = np.array([[-5.0, 5.0], [-2.0, 2.0]])
    >>> dimensionality = 2
    >>> domain = make_nd_continuous_domain(bounds, dimensionality)
    """
    input_space = {}
    for dim in range(dimensionality):
        input_space[f"x{dim}"] = ContinuousParameter(lower_bound=bounds[dim, 0], upper_bound=bounds[dim, 1])

    return Domain(input_space=input_space)
