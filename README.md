## Requirements

- Windows
- Python3
- [PyQt5 / PySide2](http://www.riverbankcomputing.co.uk/software/pyqt/intro)
## Developing

```bash
git clone https://github.com/ConnectEdge/label-me-ding.git
```
## How to build standalone executable

Below shows how to build the standalone executable on Windows.  

```bash
# install pip
python get-pip.py
# Build the standalone executable
pip install .
# if it is error "ModuleNotFoundError"
pip install qtpy
pip install pyinstaller
# run follow command
pyinstaller labelme.spec

# show version
dist/labelme --version
```