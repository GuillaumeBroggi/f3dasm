#                                                                       Modules
# =============================================================================

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

    @classmethod
    def from_file(cls, filename: Path) -> 'Domain':
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
    def from_yaml(cls: Type['Domain'], yaml: Dict[str, Dict[str, Dict[str, Any]]]) -> 'Domain':
        """Initializ a Domain from a Hydra YAML configuration file


        Notes
        -----
        The YAML file should have the following structure:
        A nested dictionary where the dictionary denote the input_space


        Parameters
        ----------
        yaml
            yaml dictionary

        Returns
        -------
            Domain class
        """
        args = {}
        for space, params in yaml.items():
            args[space] = {name: instantiate(param, _convert_="all") for name, param in params.items()}
        return cls(**args)

    def store(self, filename: str) -> None:
        """Stores the Domain in a pickle file.

        Parameters
        ----------
        filename : str
            Name of the file.
        """

        # if filename does not end with .pkl, add it
        if not filename.endswith('.pkl'):
            filename = filename + '.pkl'

        with open(filename, 'wb') as f:
            pickle.dump(self, f)

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

    def add_input_space(self, name: str, space: Parameter):
        """Add a new input parameter to the design space.

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

    def get_input_space(self) -> Dict[str, Parameter]:
        """Return the input parameters.

        Returns
        -------
        Dict[str, Parameter]
            Dictionary of input parameters.

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': ContinuousParameter(lower_bound=0., upper_bound=1.),
        ...     'param2': CategoricalParameter(categories=['A', 'B', 'C'])
        ... }
        >>> input_space = domain.get_input_space()
        >>> input_space
        {'param1': ContinuousParameter(lower_bound=0., upper_bound=1.),
        'param2': CategoricalParameter(categories=['A', 'B', 'C'])}
        """
        return self.input_space

    def get_input_names(self) -> List[str]:
        """Get the names of the input parameters.

        Returns
        -------
        List[str]
            List of the names of the input parameters.

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': ContinuousParameter(lower_bound=0., upper_bound=1.),
        ...     'param2': CategoricalParameter(categories=['A', 'B', 'C']),
        ...     'param3': DiscreteParameter(lower_bound=4, upper_bound=6)
        ... }
        >>> input_names = domain.get_input_names()
        >>> input_names
        ['param1', 'param2', 'param3']
        """
        return list(self.input_space.keys())

    def get_number_of_input_parameters(self) -> int:
        """Get the number of input parameters.

        Returns
        -------
        int
            Number of input parameters.

        Example
        -------
        >>> domain = Domain()
        >>> domain.input_space = {
        ...     'param1': ContinuousParameter(lower_bound=0., upper_bound=1.),
        ...     'param2': CategoricalParameter(categories=['A', 'B', 'C']),
        ...     'param3': DiscreteParameter(lower_bound=4, upper_bound=7)
        ... }
        >>> domain.get_number_of_input_parameters()
        3
        """
        return len(self.input_space)

    def get_continuous_input_parameters(self) -> Dict[str, ContinuousParameter]:
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
        return self.filter_parameters(ContinuousParameter).get_input_space()

    def get_continuous_input_names(self) -> List[str]:
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
        return self.filter_parameters(ContinuousParameter).get_input_names()

    def get_discrete_input_parameters(self) -> Dict[str, DiscreteParameter]:
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
        return self.filter_parameters(DiscreteParameter).get_input_space()

    def get_discrete_input_names(self) -> List[str]:
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
        return self.filter_parameters(DiscreteParameter).get_input_names()

    def get_categorical_input_parameters(self) -> Dict[str, CategoricalParameter]:
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
        return self.filter_parameters(CategoricalParameter).get_input_space()

    def get_categorical_input_names(self) -> List[str]:
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
        return self.filter_parameters(CategoricalParameter).get_input_names()

    def get_constant_input_parameters(self) -> Dict[str, ConstantParameter]:
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
        return self.filter_parameters(ConstantParameter).get_input_space()

    def get_constant_input_names(self) -> List[str]:
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
        return self.filter_parameters(ConstantParameter).get_input_names()

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
                for _, parameter in self.get_continuous_input_parameters().items()]
        )

    def filter_parameters(self, type: Type[Parameter]) -> 'Domain':
        """Filter the parameters of the design space by type

        Parameters
        ----------
        type : Type[Parameter]
            Type of the parameters to be filtered

        Returns
        -------
        Domain
            Design space with the filtered parameters

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

    def _cast_types_dataframe(self) -> dict:
        """Make a dictionary that provides the datatype of each parameter"""
        return {name: parameter._type for name, parameter in self.input_space.items()}

    def _all_input_continuous(self) -> bool:
        """Check if all input parameters are continuous"""
        return self.get_number_of_input_parameters() \
            == self.filter_parameters(ContinuousParameter).get_number_of_input_parameters()


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
    >>> design_space = make_nd_continuous_domain(bounds, dimensionality)
    """
    input_space = {}
    for dim in range(dimensionality):
        input_space[f"x{dim}"] = ContinuousParameter(lower_bound=bounds[dim, 0], upper_bound=bounds[dim, 1])

    return Domain(input_space=input_space)
