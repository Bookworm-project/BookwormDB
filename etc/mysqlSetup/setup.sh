
#ON Ubuntu:
#cp my.cnf /etc/mysql/my.cnf

#On CentOS
cp my.cnf /etc/my.cnf
cp adminMy.cnf ~/.my.cnf
mkdir /etc/mysql
ln -s /etc/my.cnf /etc/mysql/my.cnf
