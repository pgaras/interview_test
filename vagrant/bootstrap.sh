#!/bin/sh

PROVISION_DIR=/vagrant/vagrant
PROJECT_DIR=/vagrant

echo ~~~~~~~~~Authored by Peter Garas for Ocom Softwar~~~~~~~~~~~
echo ~~~~~~~~~~~~Update to latest version and links~~~~~~~~~~~~~~
export DEBIAN_FRONTEND=noninteractive
sudo ex +"%s@DPkg@//DPkg" -cwq /etc/apt/apt.conf.d/70debconf
sudo dpkg-reconfigure debconf -f noninteractive -p critical
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
sudo apt-get update

echo ~~~~~~~~~~~~Set encoding to UTF-8~~~~~~~~~~~~~~
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

echo ~~~~~~~~~~~~~~~Set Timezone ~~~~~~~~~~~~~~
rm /etc/timezone
cp ${PROVISION_DIR}/timezone /etc/timezone
sudo dpkg-reconfigure --frontend noninteractive tzdata

echo ~~~~~~~~~~~~Install required ubuntu dependencies and modules~~~~~~~~~~~~~~
# we opt to not install ubuntu's pip as it is too old and it coughs up assertion errors when running pip list command
sudo apt-get install -y python-dev libpq-dev postgresql postgresql-contrib python-lxml
# install pip
wget https://bootstrap.pypa.io/ez_setup.py -O - | python
python ${PROVISION_DIR}/get-pip.py

echo ~~~~~~~~~~~~Set up python modules~~~~~~~~~~~~~~
sudo pip install -I -r ${PROJECT_DIR}/requirements.txt