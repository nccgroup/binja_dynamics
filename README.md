# Binary Ninja Dynamic Analysis Tools

This project uses [Binjatron](https://github.com/snare/binjatron) to add live debugging to Binary Ninja.

## Installation
Inside your [Binary Ninja plugins folder](https://github.com/Vector35/binaryninja-api/tree/master/python/examples#loading-plugins), run:
```bash
git clone https://github.com/ehennenfent/binja_dynamics.git
cd binja_dynamics
./install.sh
```

## Usage
After loading a binary, click the `Enable Dynamic Analysis Tools` item in the tools menu.

## Sample Utilization

## Current Limitations
There's currently (to my knowledge) no good way to track when the user switches between open binary views, so this plugin works best when used with only a single binary open. One can make it work by reinitializing the toolbar every time one switches between binaries, but that's less than ideal. This may not be fixed until the upcoming UI API features in version 1.2.

## Requirements
* binjatron
* binja_toolbar
* PyQt5
* Binary Ninja

<NAME> has only been tested on Ubuntu 16.04. You are encouraged to file a pull request or open an issue for any incompatibilities.
