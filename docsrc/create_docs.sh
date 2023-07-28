#!/bin/bash
rm -rf source/apidoc
sphinx-apidoc -o source/apidoc ../producer
python3 edit_apidoc_modules.py
rm -rf ../docs/doctrees
rm -rf ../docs/html
make html
touch ../docs/.nojekyll
echo "<meta http-equiv='refresh' content='0; url=./html/index.html' />" > ../docs/index.html
chown -R 1000:1000 ../docs
chown -R 1000:1000 .