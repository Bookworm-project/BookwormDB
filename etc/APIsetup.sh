read -p "What folder should be used to hold the bookworm cgi-bin scripts?
This will make that into a git repository for Bookworm.
Easiest (but possibly incompatible with existing cgi scripts) is to make this
your existing cgi-bin directory.
 " cgidir

if [ $(grep -c "/" cgidir) -ne 0 ]
then
    mkdir -p $cgidir
    git clone http://github.com/bmschmidt/BookwormAPI.git $cgidir
else
    echo "Not cloning because no slash in filename"
fi

read -p "What folder will hold the d3 scripts?
This folder
 " d3dir

if [ $(grep -c "/" d3dir) -ne 0 ]
then
    mkdir -p $d3dir
    git clone http://github.com/bmschmidt/BookwormD3.git $d3dir
else
    echo "Not cloning because no slash in filename"
fi
#install numpy
wget http://sourceforge.net/projects/numpy/files/NumPy/1.6.2/numpy-1.6.2.tar.gz/download
tar -xzvf numpy-1.6.2.tar.gz
cd numpy-1.6.2.tar.gz
python setup.py install
cd ..

#install python-json
#yum install python-json

#Set up query logging.
mkdir /var/log/presidio
touch /var/log/presidio/log.txt
chmod -R 777 /var/log/presidio


mkdir /var/www/.python-eggs

