perl -ne 'chomp;$_ =~ m/(.*)(\d\d\d\d)(\.txt)/;
print "{\"date\":\"" . $2 . "\"," . "\"corpus\":\"" . $1 . "\"" . "," . "\"filename\":\"".$1.$2."\"".","."\"searchstring\":\"http:\/\/books.google.com\"}\n";
' filenames.txt > ../metadata/jsoncatalog.txt
