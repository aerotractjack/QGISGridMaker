#!/bin/bash

mkdir -p /home/aerotract/software/ValidationPlotGen/QGISGridMaker
pushd /home/aerotract/software/ValidationPlotGen/QGISGridMaker
rm -rf *.egg-info/ dist/ build/
/usr/bin/python3 setup.py sdist bdist_wheel
/usr/bin/python3 -m pip install --upgrade --force-reinstall dist/qgisgridmaker-0.1-py3-none-any.whl
popd