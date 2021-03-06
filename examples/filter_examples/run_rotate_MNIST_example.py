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

from dpemu.nodes import Array, Series
from dpemu.filters.image import Rotation
from dpemu.dataset_utils import load_mnist


def main():
    """An example that rotates MNIST digits and displays one.
    Usage: python run_rotate_MNIST_example <angle>
    where <angle> is the angle of rotation
    (e.g. 90 to rotate by pi / 2)
    """
    x, _, _, _ = load_mnist()
    xs = x[:20]                 # small subset of x
    angle = float(sys.argv[1])
    print(f"x subset shape: {xs.shape}")
    img_node = Array(reshape=(28, 28))
    root_node = Series(img_node)
    img_node.addfilter(Rotation("angle"))
    result = root_node.generate_error(xs, {'angle': angle})

    plt.matshow(result[0].reshape((28, 28)))
    plt.show()


if __name__ == "__main__":
    main()
