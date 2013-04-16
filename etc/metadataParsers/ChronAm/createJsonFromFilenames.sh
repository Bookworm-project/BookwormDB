
cat ../../../files/downloads/filenames | sed 's/^.\///' | perl -ne '
use JSON;
$_ =~ s/ocr.txt/ocr/;
if ($_ =~ m/([^\/]+)\/([^\/]+)\/([^\/]+)\/([^\/]+)\/ed-([^\/]+)\/seq-([^\/]+)\/(ocr)/) {
    chomp; 
    $filename = $_; 
    print encode_json(
      {"paperid",$1,"date",$2 . "-" . $3 . "-" . $4,"filename",$filename,"edition",$5,"page",$6}) . "\n"}
' > ../../../files/metadata/jsoncatalog.txt
