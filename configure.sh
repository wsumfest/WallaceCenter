# This script sets up the neccesary packages on a mac
#setup pip
touch get-pip.py
curl https://bootstrap.pypa.io/get-pip.py >> get-pip.py
sudo python get-pip.py
rm -f get-pip.py

#Geoiplookup
brew install geoip
brew install geoipupdate
geoipupdate

#dotenv to load developer keys
sudo pip install -U python-dotenv

# Set up vcrpy for testing
sudo pip install -U vcrpy

# Set up requests for http requests
sudo pip install -U requests

#Build for google api calls
# sudo pip install --ignore-installed google-api-python-client
sudo pip install -I google-api-python-client==1.3.2

#Oath2 package for google api
sudo pip install --ignore-installed oauth2client

#Gspread for verifying searches
sudo pip install --ignore-installed gspread

#Openpyxl for local verification systems
sudo pip install --ignore-installed openpyxl

#Numpy, Scipy, matplotlib for statistical anaylsis 
sudo pip install --ignore-installed scipy
sudo pip install --ignore-installed numpy
sudo pip install --ignore-installed matplotlib
sudo pip install --ignore-installed pandas
sudo pip install --ignore-installed patsy
sudo pip install --ignore-installed statsmodels

#Graphviz
sudo pip install graphviz 


chmod u+x keyword_simulations.sh
chmod u+x clear_logs.sh

SIX=$(pip show six | grep "Location:" | cut -d " " -f2)
echo "export PYTHONPATH=$PYTHONPATH:$SIX" >> ~/.bash_profile
source ~/.bash_profile
