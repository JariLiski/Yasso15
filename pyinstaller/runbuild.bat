cd ..
python C:\Python25\Scripts\f2py.py -c --fcompiler=gnu95 -m y07 y07_subroutine.f90
cd pyinstaller
python c:\pyinstaller\Build.py yasso.spec
cd ..
copy demo_data.txt pyinstaller\dist
copy yasso_param.dat pyinstaller\dist
cd pyinstaller\dist
yasso
cd ..
