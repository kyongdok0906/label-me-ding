# Guide Labelme 
## 1. Setting
The python must to install on system.  python  >= v 3.x 

The python can download in <a href="https://www.python.org/downloads/">here</a> .

## 2 For development
### install pip 

python -m pip install --upgrade pip

or

python -m pip install --upgrade --force-reinstall pip

### install pyinstaller
pip install pyinstaller

### install all package 

python setup.py install

## 3 How to build an independent app that runs in Wondow

pyinstaller labelme.spec

### Build path
dist/labelme.exe
