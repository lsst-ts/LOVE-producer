#!/bin/bash
rm -rf source/apidoc
sphinx-apidoc -o source/apidoc ../python/love ../python/love/producer/test_utils/*
python edit_apidoc_modules.py
rm -rf ../docs/doctrees
rm -rf ../docs/html
make html
touch ../docs/.nojekyll
echo "<meta http-equiv='refresh' content='0; url=./html/index.html' />" > ../docs/index.html
