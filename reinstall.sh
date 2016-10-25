#!/usr/bin/env bash
rm -rf dist/;
python setup.py sdist;
pip uninstall -y django-mongolog;
pip install dist/*
