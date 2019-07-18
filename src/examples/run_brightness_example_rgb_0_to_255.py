import time
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

import src.problemgenerator.array as array
import src.problemgenerator.filters as filters


def main():
    img_path = "demo/landscape.png"
    d = {"tar": 1, "rat": 0.55, "range": 255}

    # Use the looped version
    img1 = Image.open(img_path)
    data1 = np.array(img1)
    x_node1 = array.Array(data1.shape)
    b1 = filters.Brightness("tar", "rat", "range")
    x_node1.addfilter(b1)
    start1 = time.time()
    result1 = x_node1.generate_error(data1, d)
    end1 = time.time()
    print(f"Time traditional: {end1-start1}")

    # Use the vectorized version
    img2 = Image.open(img_path)
    data2 = np.array(img2)
    x_node2 = array.Array(data2.shape)
    b2 = filters.BrightnessVectorized("tar", "rat", "range")
    x_node2.addfilter(b2)
    start2 = time.time()
    result2 = x_node2.generate_error(data2, d)
    end2 = time.time()
    print(f"Time vectorized: {end2-start2}")

    print()
    print(f"Trad type: {result1.dtype}")
    print(f"Vectorized type: {result2.dtype}")
    abs_diff = np.abs(result1.astype(int) - result2.astype(int))
    insignificant = len(abs_diff[abs_diff > 1]) == 0
    print(f"Absolute Difference at most 1: {insignificant}")
    if not insignificant:
        abs_diff

    fig, ax = plt.subplots(1, 2)
    ax[0].imshow(result1)
    ax[0].set_title("Traditional")
    ax[1].imshow(result2)
    ax[1].set_title("Vectorized")
    plt.show()


if __name__ == "__main__":
    main()