#! usr/bin/perl
use LWP::Simple;
use LWP::UserAgent;
use HTTP::Request;
use HTTP::Response;
use HTML::LinkExtor; # allows you to extract the links off of an HTML page.
use Lingua::EN::Sentence qw( get_sentences add_acronyms );
use strict;
use warnings;
use Data::Dumper;
use CGI qw(:cgi);
require("/users/bschmidt/Documents/Data/Internet_Archive/perlscripts/python calls.pl");
use Term::ProgressBar 2.00;
use feature qw(switch say state);


my $catalog_subset = shift;
my $dbh = get_dbh();


my %catinfo = load_relevant_bookids("WHERE ".$catalog_subset . "=1", "ocaid",("year",$catalog_subset));


clean_texts(keys %catinfo);
sub clean_texts {
    my (@filenames) = @_;
    die "EMPTY LIST" if ($#filenames == -1);
    #fisher_yates_shuffle( \@filenames); #Process them in a random order so I can test better.
    my $max = $#filenames; my $next_update = 0; my $i = 0;
	my $progress = Term::ProgressBar->new({name  => 'Cleaning Texts from the list',
                                        count =>  $max,
                                        ETA   => 'linear', });
	$progress->max_update_rate(1);
    foreach my $filename (@filenames) {
        if (!-e "/Volumes/Rameau's Nephew/IAtexts/Downloads/$filename.txt") {iadownload($filename);}
        if (-e "/Volumes/Rameau's Nephew/IAtexts/Downloads/$filename.txt") {
            open (FH, "/Volumes/Rameau's Nephew/IAtexts/Downloads/$filename.txt" ) or warn "$1\n";
            if (!-e "/Volumes/Rameau's Nephew/IAtexts/Cleaned/$filename.txt") {
                open (OUTPUT, ">/Volumes/Rameau's Nephew/IAtexts/Cleaned/$filename.txt") or warn "$!";
                #If it's a Google books, I have to wait for that boilerplate text at the beginning to end before scanning
                my $googswitch = 0;
                my $needs_goog_switch = 0; $needs_goog_switch = 1 if $filename =~ m/goog$/gi; #
                my $linenumber = 0;
                while (my $line = <FH>) {
                    $linenumber++;
                    if ($googswitch == 1 || $needs_goog_switch == 0) {
                        #The order of these regexes are important
                        # ????              ##something to clear out chapter headings It might use something about a pagenumber, or about capital letters
                        #$line =~ s/^\s*$/thisisanewlineplaceholder/g; #replace empty lines with a placeholder for newlines.
                            #I'm not doing this now, b/c I think joining some non-sentences and shortening the files is better than
                            #losing lots of sentences over page breaks and making the files more cumbersome. It loses paragraph information, though.
                        if ($line =~ m/[A-Z]{3}/) { #This deletes lines that are mostly uppercase letters.
                            my $temp = $line;
                            $temp =~ s/[A-Z]//g; #Set to lowercase
                            if (length($temp)/length($line) <= 0.5) {
                                $line = "";
                            }
                        }                        
                        $line =~ s/- *[\n\r]//g; #hyphenated words at lineend
                        $line =~ s/[\n\r]/ /g; #remove newlines
                        #$line =~ tr/[A-Z]/[a-z]/; #Set to lowercase--I'M GOING TO SWITCH THIS TO THE LATER SCRIPT
                        $line =~ s/[\.\?!](["'\)])/$1\./g; #Move period to end of sentence
                        $line =~ s/[\.\?!](["'\)])/$1\./g; #Move period to end of sentence again, in case there's double quotes or a period and parenthesis or something
                        $line =~ s/"/''/g; #CHANGE QUOTES TO DOUBLE to make them safer for mysql                  
                        ##COMMON ABBREVIATIONS NOT TO END SENTENCES ON
                        $line =~ s/ (mr|ms|mrs|dr|prof|rev|rep|sen|st|sr|jr|ft|gen|adm|lt|col|a-z)\./ $1/gi; #common abbreviation exceptions--in rare cases, this will strip out a sentence completion that should be there.                        
                        $line =~ s/^(mr|ms|mrs|dr|prof|rev|rep|sen|st|sr|jr|ft|gen|adm|lt|col|a-z)\./$1/gi; #Abbreviations can start with a newline as well as a space.                        
                        $line =~ s/^(mr|ms|mrs|dr|prof|rev|rep|sen|st|sr|jr|ft|gen|adm|lt|col|a-z)\./$1/gi; #Abbreviations can start with a newline as well as a space.                        
                        #NEEDS SOMETHING FOR STRINGS LIKE "E.G. Boring" OR "U.S.A."; or else just use nltk for this
                        $line =~ s/([\.!\?]) */$1thisisanewlineplaceholder/g; #replace sentence punctuation with newline--this is still bad with abbreviations, maybe I need a longer list of exceptions?
                        $line =~ s/([\.!\?])$/$1thisisanewlineplaceholder/g; #Punctuation can come at the end of the line, too
                        $line =~ s/^.*digitize?d?.? by.*$//gi;                       
                        $line =~ s/^.*([vli]j|[gq])oo[gqs] ?[il1][ce].*$//gi; #kill any lines that have Google-matching keywords in them.
                        $line =~ s/^.*googl.*$//gi; #kill any lines that have Google-matching keywords in them.
                        $line =~ s/[^ a-zA-Z,'-\.!\?\(\):;0-9]//g; #replace all but a few punctuators and digits with nothing (the rest will come out in python)
                        $line =~ s/  +/ /; #Replace multiple spaces with a single space
                        $line =~ s/thisisanewlineplaceholder/\n/g; #put newlines at the end of sentences.
                        print OUTPUT "$line";
                    }
                    if ($line =~ m/[gq]oo[gq][li1]e\W*com/gi) {$googswitch = 1;}# $switchedat = $linenumber; print "Switching:\t"}
                }
            }
            close (FH);
            close (OUTPUT);
            $next_update = $progress->update($i) if $i++ >= $next_update;	
        }
    }
}
