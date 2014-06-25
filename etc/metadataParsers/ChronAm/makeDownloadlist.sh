cat jsoncatalog.txt | perl -e 'while (<>) {$_ =~ m/(http[^"]*seq-\d+)/; $base = $1; $_ =~ m/"filename": "([\w\d\/_-]+)"/; $file = $1; print "curl -L -o $file $base/ocr.txt\n"}' > downloadAll.sh
