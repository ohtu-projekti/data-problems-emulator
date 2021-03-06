Installing dpEmu
================

**Works only with Python versions 3.6 and 3.7**

To install dpEmu on your computer, execute the following commands in your terminal:

.. code-block:: bash

    git clone https://github.com/dpEmu/dpEmu.git
    cd dpEmu
    python3 -m venv venv
    source venv/bin/activate
    pip install -U pip setuptools wheel
    pip install -r requirements/base.txt
    pip install -e "git+https://github.com/cocodataset/cocoapi.git#egg=pycocotools&subdirectory=PythonAPI"
    pip install -e .

In order to run all of the examples, you'll also need to execute the following command:

.. code-block:: bash

    pip install -r requirements/examples.txt

Additionally, run the following command in order to locally build the documentation with Sphinx:

.. code-block:: bash

    pip install -r requirements/docs.txt

Object detection example and notebooks requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**CUDA and cuDNN installations required**

Execute the following commands after all of the above:

.. code-block:: bash

    git clone https://github.com/dpEmu/Detectron.git libs/Detectron
    ./scripts/install_detectron.sh
    git clone https://github.com/dpEmu/darknet.git libs/darknet
    ./scripts/install_darknet.sh
