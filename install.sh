sudo apt update
sudo apt install git lldb gdb
sudo apt install python-pyqt5 python-pip python-dev python-apt
sudo -H pip install --upgrade pip
sudo -H pip install -r ~/.binaryninja/plugins/binja_voltron_toolbar/requirements.txt

cd ~/.binaryninja/plugins
git clone https://github.com/ehennenfent/binja_toolbar.git
git clone https://github.com/ehennenfent/binja_spawn_terminal.git
git clone https://github.com/ehennenfent/binjatron.git
git clone https://github.com/ehennenfent/hexview.git

cd ~/Downloads
git clone https://github.com/snare/voltron
cd voltron
./install.sh
