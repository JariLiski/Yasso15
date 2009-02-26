#!/bin/sh
python ~/pyinstaller/Build.py yasso.spec
cp ../demo_data.txt dist/
cp ../yasso_param.dat dist/
dist/yasso
