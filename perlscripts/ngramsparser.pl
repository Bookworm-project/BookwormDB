#!usr/bin/perl

#First run this query on words: SELECT SUM(words),year FROM (SELECT * from 1grams where word="the" or word = 'that' or word = 'which' or word = 'of' or word = 'to')as mytab WHERE BINARY(word) = "the" OR BINARY(word) = "that" OR BINARY(word)= 'which' OR BINARY(word) = "of" OR BINARY(word) = "to" GROUP BY year INTO OUTFILE '/tmp/totcounts.txt'. I should actually have had this in there twice: 

my $ngramsdir = shift or die $!; #This takes a directory name as input
opendir (DIR,$ngramsdir) or die "Not a valid directory";
@FILES  = readdir(DIR);

my %wordlist = ();

open (BASELINEFILE, '/tmp/totcounts.txt') or die "No such file";
print "STDOUT is working\n";
my %yearcounts = ();
while (my $string = <BASELINEFILE>) {
    chomp $string;
    print $string. "\n";
    ($count,$year) = split("\t",$string);
    if ($year >= 1701) {
	$yearcounts{$year} = $count;
    }
}

foreach my $year (keys %yearcounts) {
    print "$year $yearcounts{$year}\n";
}

open (OUTPUT,">$ngramsdir/../Googlist.txt"); #place the list one folder down

foreach my $file (@FILES) {
    %wordlist = ();
    print "working on $file \n";
    open (INPUT,"$ngramsdir/$file");
    while (my $string = <INPUT>) {
      	($word, $year, $count, $pages, $books) = split("\t",$string);
	$wordlist{$word}[0] += $count;
	$wordlist{$word}[1] += $books;
	if ($year >= 1701) {
	    $wordlist{$word}[2] += $count/$yearcounts{$year};
	}
    }
    foreach my $word (keys %wordlist) {
	my $lowercase = lc($word);
	my $normfreq = $wordlist{$word}[2]/scalar(keys(%yearcounts))*1000000;
	print OUTPUT "$word\t$wordlist{$word}[0]\t$wordlist{$word}[1]\t$normfreq\t$lowercase\n";
    }
}

close (OUTPUT);
print "Starting sorting";
`sort -nrk 4 $ngramsdir/../Googlist.txt > $ngramsdir/../sorted.txt`;

