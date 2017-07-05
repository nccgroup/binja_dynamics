sudo apt update
sudo apt install git lldb gcc
sudo apt install python-pyqt5 python-pip python-dev python-apt
sudo -H pip install --upgrade pip
sudo -H pip install -r requirements.txt

cd ~/.binaryninja/plugins
git clone https://github.com/ehennenfent/binja_toolbar.git
git clone https://github.com/ehennenfent/binja_spawn_terminal.git
git clone https://github.com/ehennenfent/binjatron.git
cd ~/binaryninja/plugins/binja_dynamics/memory_viewer
git clone https://github.com/ehennenfent/hexview.git

cd ~/Downloads
sudo apt install help2man autoconf automake texinfo bison
git clone git://git.sv.gnu.org/m4
cd m4
git checkout -b branch-1.4 origin/branch-1.4
./bootstrap
./configure
make
sudo make install

cd ~/Downloads
sudo apt remove gdb
git clone git://sourceware.org/git/binutils-gdb.git
cd binutils-gdb
./configure --enable-tui --with-python
make
sudo make install

cd ~/Downloads
git clone https://github.com/snare/voltron
cd voltron
./install.sh
