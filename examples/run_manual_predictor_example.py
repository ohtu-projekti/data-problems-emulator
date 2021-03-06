# MIT License
#
# Copyright (c) 2019 Tuomas Halvari, Juha Harviainen, Juha Mylläri, Antti Röyskö, Juuso Silvennoinen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys

import matplotlib.pyplot as plt
import numpy as np

from dpemu import runner
from dpemu.plotting_utils import visualize_scores, print_results_by_model, visualize_best_model_params
from dpemu.nodes import Array
from dpemu.filters.common import GaussianNoise


class Preprocessor:
    def run(self, train_data, test_data, params):
        return train_data, test_data, {}


class PredictorModel:
    def run(self, train_data, test_data, params):
        # The model tries to predict the values of test_data
        # by using a weighted average of previous values
        estimate = 0
        squared_error = 0

        for elem in test_data:
            # Calculate error
            squared_error += (elem - estimate) * (elem - estimate)
            # Update estimate
            estimate = (1 - params["weight"]) * estimate + params["weight"] * elem

        mean_squared_error = squared_error / len(test_data)

        return {"MSE": mean_squared_error}


def get_data(argv):
    train_data = None
    test_data = np.arange(int(sys.argv[1]))
    return train_data, test_data


def get_err_root_node():
    # Create error generation tree that has an Array node
    # as its root node and a GaussianNoise filter
    err_root_node = Array()
    err_root_node.addfilter(GaussianNoise("mean", "std"))
    return err_root_node


def get_err_params_list():
    # The standard deviation goes from 0 to 20
    return [{"mean": 0, "std": std} for std in range(0, 21)]


def get_model_params_dict_list():
    # The model is run with different weighted estimates
    return [{
        "model": PredictorModel,
        "params_list": [{'weight': w} for w in [0.0, 0.05, 0.15, 0.5, 1.0]],
        "use_clean_train_data": False
    }]


def visualize(df):
    # Visualize mean squared error for all used standard deviations
    visualize_scores(
        df=df,
        score_names=["MSE"],
        is_higher_score_better=[False],
        err_param_name="std",
        title="Mean squared error"
    )
    visualize_best_model_params(
        df=df,
        model_name="Predictor #1",
        model_params=["weight"],
        score_names=["MSE"],
        is_higher_score_better=[False],
        err_param_name="std",
        title=f"Best model params"
    )

    plt.show()


def main(argv):
    # Create some fake data
    if len(argv) == 2:
        train_data, test_data = get_data(argv)
    else:
        exit(0)

    # Run the whole thing and get DataFrame for visualization
    df = runner.run(
        train_data=train_data,
        test_data=test_data,
        preproc=Preprocessor,
        preproc_params=None,
        err_root_node=get_err_root_node(),
        err_params_list=get_err_params_list(),
        model_params_dict_list=get_model_params_dict_list()
    )

    print_results_by_model(df)
    visualize(df)


if __name__ == "__main__":
    main(sys.argv)
