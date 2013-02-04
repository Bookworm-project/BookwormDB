git clone http://github.com/bmschmidt/BookwormAPI.git /var/www/cgi-bin
git clone http://github.com/bmschmidt/BookwormD3.git /var/www/d3

#install numpy
wget http://sourceforge.net/projects/numpy/files/NumPy/1.6.2/numpy-1.6.2.tar.gz/download
tar -xzvf numpy-1.6.2.tar.gz
cd numpy-1.6.2.tar.gz
python setup.py install

mkdir /var/log/presidio
touch /var/log/presidio/log.txt
chmod -R 777 /var/log/presidio

mkdir /var/www/.python-eggs

yum install python-json