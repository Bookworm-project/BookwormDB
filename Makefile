ubuntu-install:
	apt-get install python-numpy python-mysqldb
	mkdir -p /var/log/presidio
	touch /var/log/presidio/log.txt
	chown -R www-data:www-data /var/log/presidio
	mv ./*.py /usr/lib/cgi-bin/
	chmod -R 755 /usr/lib/cgi-bin

os-x-install:
	brew install python-numpy python-mysqldb
	mkdir -p /var/log/presidio
	touch /var/log/presidio/log.txt
	chown -R www /var/log/presidio
	chmod -R 755 /usr/lib/cgi-bin	
	mkdir -p /etc/mysql
	ln -s /etc/my.cnf /etc/mysql/my.cnf 
