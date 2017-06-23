# Binary Ninja Dynamic Analysis Tools

This project uses [Binjatron](https://github.com/snare/binjatron) to add live debugging to Binary Ninja.

## Installation
Inside your [Binary Ninja plugins folder](https://github.com/Vector35/binaryninja-api/tree/master/python/examples#loading-plugins), run:
```bash
git clone https://github.com/ehennenfent/binja_dynamics.git
cd binja_dynamics
./install.sh
```

## Components
* Debugger toolbar
* Register viewer
* Stack viewer
* Backtrace viewer

## Documentation
This project is intended to help beginners gain insight into the way binaries execute. Please consult [the wiki](https://github.com/ehennenfent/binja_dynamics/wiki) for helpful examples that may aid you in getting started.

## Usage
After loading a binary, click the `Enable Dynamic Analysis Tools` item in the tools menu.

## Current Limitations
* binja_dynamics has only been tested on Ubuntu 16.04. You are encouraged to file a pull request or open an issue for any incompatibilities.
* Since Binary Ninja and binjatron are based on Python 2.7, the version of GDB that ships with Ubuntu must be replaced with a version that supports Python 2.7 before binja_dynamics is installed. See [this thread](https://askubuntu.com/a/577088) for assistance with that.
* See [Issues](https://github.com/ehennenfent/binja_dynamics/issues) for more

## Third-party Components
* binja_dynamics makes use of a [fork](https://github.com/ehennenfent/hexview) of [qthexedit](https://github.com/csarn/qthexedit), which is licensed under GPLv2.
* The images used for icons are licensed under Creative Commons. See [attribution.txt](https://github.com/ehennenfent/binja_dynamics/blob/master/attribution.txt) for information on the sources.

## Requirements
* [binjatron](https://github.com/snare/binjatron)
* [binja_toolbar](https://github.com/ehennenfent/binja_toolbar)
* [binja_spawn_terminal](https://github.com/ehennenfent/binja_spawn_terminal.git)
* [voltron](https://github.com/snare/voltron)
* PyQt5
* Binary Ninja

Excluding Binary Ninja, `install.sh` will handle these dependencies for you.
