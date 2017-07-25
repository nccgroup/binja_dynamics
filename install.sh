# Install base dependencies from apt
sudo apt update
sudo apt install git lldb gcc

# Install python dependencies for plugins
sudo apt install python-pyqt5 python-pip python-dev python-apt
sudo -H pip install --upgrade pip
sudo -H pip install -r requirements.txt

# Clone plugin dependencies
cd ~/.binaryninja/plugins
git clone https://github.com/ehennenfent/binja_toolbar.git
git clone https://github.com/ehennenfent/binja_spawn_terminal.git
git clone https://github.com/snare/binjatron.git
cd ~/binaryninja/plugins/binja_dynamics/memory_viewer
git clone https://github.com/ehennenfent/hexview.git

# Install dependencies for gdb and m4
sudo apt install binutils binutils-dev binutils-source
sudo apt install help2man autoconf automake texinfo bison flex
# Terminal UI dependencies for GDB
sudo apt install libncurses5 libncurses5-dev libncursesw5 libncursesw5-dev

# Install m4 from source (3 years ahead of version in apt)
cd ~/Downloads
git clone git://git.sv.gnu.org/m4
cd m4
git checkout -b branch-1.4 origin/branch-1.4
./bootstrap
./configure
make
sudo make install

cd ~/Downloads
# Remove existing version of gdb if present
sudo apt remove gdb
git clone git://sourceware.org/git/binutils-gdb.git
cd binutils-gdb
./configure --enable-tui --with-python
make
# Precompile binutils from git (assuming that step already failed)
cd binutils
./configure
make
sudo make install
cd ..
./configure --enable-tui --with-python
make
sudo make install

# Add dependencies for 32 bit binaries
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install libc6:i386 libncurses5:i386 libstdc++6:i386

cd ~/Downloads
git clone https://github.com/snare/voltron
cd voltron
./install.sh
