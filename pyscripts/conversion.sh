# script to convert metadata into bookid file that can be loaded into mySQL
# first gets bookid from filename, then sets up associative array for the 
# months, so that Jan=01, Feb=02, etc.  
# awk looks at each line and executes /pattern/ {action}
# so for the Date: line, this will create a date string, and for the Categories
# line, this will print out bookid, datetime string, and category id
#
# first argument should be the directory where the .abs files live
# second argument should be the catalog file
for i in $1/* 
do 
    fn=$(basename $i); 
    fn=${fn%.*};
    id=$(grep -m 1 $fn $2 | cut -f1)
    if [ -n "$id" ]
    then
	awk -v x=$id 'BEGIN{a["Dec"] = "12"; a["Jan"]="01"; a["Feb"] = "02";}/^Date:/{ds=sprintf("%s-%s-%02d %s",$5,a[$4],$3,$6)}/^Categories/{match($2,"\\."); if (RSTART==0) {print x "\t"ds "\t" $2;} else print x "\t" ds "\t" substr($2,0,RSTART-1);}' $i; 
    fi
done
