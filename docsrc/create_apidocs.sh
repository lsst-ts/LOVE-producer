#!/bin/bash
rm -rf source/apidoc
sphinx-apidoc -o source/apidoc ../python/love ../python/love/producer/test_utils/*
python edit_apidoc_modules.py
