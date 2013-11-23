ubuntu-install:
	apt-get install python-numpy python-mysqldb
	mkdir /var/log/presidio
	touch /var/log/presidio/log.txt
	chown -R www-data:www-data /var/log/presidio
	mv ./*.py /usr/lib/cgi-bin/
	chmod -R 755 /usr/lib/cgi-bin
