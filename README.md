## Requirements

- Windows
- Python3
- [PyQt5 / PySide2](http://www.riverbankcomputing.co.uk/software/pyqt/intro)
## fetch from github

```bash
git clone https://github.com/ConnectEdge/label-me-ding.git
```

## for Developing
```bash
# install pip
python get-pip.py
pip install -r requirements-dev.txt  

# if it is error "ModuleNotFoundError"
pip install qtpy
pip install pyinstaller
```
## Below shows how to build the standalone executable on Windows.  

```bash
# run follow command
pyinstaller labelme.spec

# show version
dist/labelme --version
```