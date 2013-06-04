#!/usr/bin/sh
#must be run from the presidio directory

#This adds a cron job, set for reboot, that runs a (newly created) script.

#find the directory
path=`pwd`;

#make the program to be executed
echo "
#!/usr/bin/sh
sleep 20;
mysql < $path/files/createTables.SQL;
" > startup.sh;

chmod +x startup.sh;

#copy the existing cron file, and add a reboot event
#replace existing chronjobs on this particular directory

crontab -l | grep -v $path > tmp.cron
echo "@reboot $path/startup.sh" >> tmp.cron

#make that the cron events.
crontab tmp.cron


