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

import numpy as np
from dpemu.nodes import Array, Series
from dpemu.filters.text import OCRError
from dpemu.filters.common import ApplyWithProbability

data = np.array([["a"], ["a"], ["a"], ["a"], ["a"], ["a"], ["a"], ["a"], ["a"], ["a"]])

params = {"a": [["e"], [1.0]]}
ocr = OCRError("ocr_params", "ocr_p")

x_node = Array()
x_node.addfilter(ApplyWithProbability('ocr', 'p'))
root_node = Series(x_node)

out = root_node.generate_error(data, {'ocr_params': params, 'ocr_p': 1.0, 'ocr': ocr, 'p': 0.5})

print(out)
print("output shape:", out.shape, ", output dtype:", out.dtype)