from dataclasses import dataclass, field

import autograd.numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from ..base.design import DesignSpace


@dataclass
class Data:
    """Class that contains data

    :param data: data stored in a DataFrame
    :param design: designspace
    """

    design: DesignSpace
    data: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.data = self.design.get_empty_dataframe()

    def reset_data(self):
        """Reset the dataframe to an empty dataframe with the appropriate input and output columns"""
        self.__post_init__()

    def show(self):
        """Print the data to the console"""
        print(self.data)
        return

    def add(self, data: pd.DataFrame, ignore_index: bool = False):
        """Add data

        :param data: data to append
        """
        self.data = pd.concat([self.data, data], ignore_index=ignore_index)

        # Apparently you need to cast the types again
        # TODO: Breaks if values are NaN or infinite
        self.data = self.data.astype(self.design._cast_types_dataframe(self.design.input_space, "input"))
        self.data = self.data.astype(self.design._cast_types_dataframe(self.design.output_space, "output"))

    def add_output(self, output: np.ndarray, label: str = "y"):
        """Add a numpy array to the output column of the dataframe

        :param output: Output data
        :param label: label of the output column to add to
        """
        self.data[("output", label)] = output

    def add_numpy_arrays(self, input: np.ndarray, output: np.ndarray):
        """Append a numpy array to the dataframe

        :param input: 2d numpy array added to input data
        :param output: 2d numpy array added to output data
        """
        df = pd.DataFrame(np.hstack((input, output)), columns=self.data.columns)
        self.add(df, ignore_index=True)

    def remove_rows_bottom(self, number_of_rows: int):
        """Remove a number of rows from the end of the Dataframe

        :param number_of_rows: number of rows to remove from the bottom
        """
        if number_of_rows == 0:
            return  # Don't do anything if 0 rows need to be removed

        self.data = self.data.iloc[:-number_of_rows]

    def get_input_data(self) -> pd.DataFrame:
        """Get the input data

        :returns: DataFrame containing only the input data
        """
        return self.data["input"]

    def get_output_data(self) -> pd.DataFrame:
        """Get the output data

        :returns: DataFrame containing only the output data
        """
        return self.data["output"]

    def get_n_best_output_samples(self, nosamples: int) -> pd.DataFrame:
        """Returns the n lowest rows of the dataframe. Values are compared to the output columns

        :param nosamples: number of samples
        :returns: DataFrame containing the n best samples
        """
        return self.data.nsmallest(n=nosamples, columns=self.design.get_output_names())

    def get_n_best_input_parameters_numpy(self, nosamples: int) -> np.ndarray:
        """Returns the input vectors in numpy array format of the n best samples

        :param nosamples: number of samples

        :returns: numpy array containing the n best input parameters
        """
        return self.get_n_best_output_samples(nosamples)["input"].to_numpy()

    def get_number_of_datapoints(self) -> int:
        """Get the total number of datapoints

        :returns: total number of datapoints
        """
        return len(self.data)

    def plot(self, input_par1: str, input_par2: str = None):
        """Plot the data of two parameters in a figure

        :param input_par1: name of first parameter (x-axis)
        :param input_par2: name of second parameter (x-axis)
        """
        fig, ax = plt.figure(), plt.axes()

        ax.scatter(self.data[("input", input_par1)], self.data[("input", input_par2)], s=3)

        ax.set_xlabel(input_par1)
        ax.set_ylabel(input_par2)

        return fig, ax

    def plot_pairs(self):
        """
        Plot a matrix of 2D plots that visualize the spread of the samples for each dimension.
        Requires seaborn to be installed.
        """
        import seaborn as sb

        sb.pairplot(data=self.get_input_data())
