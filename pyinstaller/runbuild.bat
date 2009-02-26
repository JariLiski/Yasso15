python c:/pyinstaller/Build.py yasso.spec
cd ..
copy demo_data.txt pyinstaller\dist
copy yasso_param.dat pyinstaller\dist
cd pyinstaller\dist
yasso