#!/bin/sh
cd ..
f2py2.5 -m y07 y07_subroutine.f90
f2py2.5 -c --fcompiler=gnu95 -m y07 y07_subroutine.f90
cd pyinstaller
python ~/pyinstaller/Build.py yasso_linux.spec
cp ../demo_data.txt dist/
cp ../yasso_param.dat dist/
dist/yasso
