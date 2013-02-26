#! usr/bin/perl
use strict;
use warnings;

my @z = <>;
#This is a perl script that accepts text from STDIN and tokenizes it in a human readable format that serves as a good interchange for serious data parsing. It is optimized for use with Internet Archive books, but may have problems with them. It attempts to follow the rules for tokenizing laid out in the Michel-Aiden supplemental materials in science, using whitespace as a delimiter between words; in addition, it attempts to use English language punctuation rules to identify the ends of sentences and indicates those using a newline character.
# For other western languages, it will separate at sentences but be overaggressive in breaking at periods that appear for other reasons;
# For non-western languages, it may behave strangely, but should at least split unicode strings up at spaces and remove punctuators.
#--Ben Schmidt

#It's in perl because Python versions were murderously slow, and control flow is too hard in awk for all these regexes.

#Here are some options that may be customized with values that evaulate true or false:
#Whether to strip Google Book scan language (also removes texts legitimately about Google):

#All these options should be set to zero before pushing to the main branch.

my $use_goog_switch = 0;

#Whether to ignore html files (which are often "File not Found" pages from webcrawling)
my $strip_html = 0;

#Whether to skip files that are 
my $skip_mostly_uppercase=0;


###################
### End options ###
###################

##Google files start with boilerplate about the book being scanned by google: this figures out how to ignore that.
#Only important for Internet Archive books, but that's where the codebase started.
my $googswitch = 0;
my $needs_goog_switch = 0;
my $linenumber = 0;

#Google books need the first page stripped because they have that first page included.
#This will not work on things that contain the word "Google" legimately; them's the breaks, for now.

my $checkrange = 0;

if ($use_goog_switch) {
    #It checks every line in the first 75 to see if the word "Google" appears: if it's there, we determine that we'll only write once we get past the Google headers.
    $checkrange=75
}

if ($#z < $checkrange) {$checkrange = $#z} 
if ($use_goog_switch) {
    foreach my $i (0..$checkrange) {
	if ($z[$i] =~ m/Google/) {
	    $needs_goog_switch = 1;
	}
    }
}
#This just ignores the ones that are HTML junk--other files will have to be handled differently.
if ($strip_html) {
    if ($z[0] =~ m/html/) {
	die;
    }
}

#Why?
print " ";

#Keep track of how long it is: break at newlines if more than 64,000 characters, since awk can't handle more than 32,000 columns
my $currentlength=0;

foreach my $line (@z) {
    $linenumber++;
    if ($googswitch == 1 || $needs_goog_switch == 0) {
	#The order of these regexes are important

	my $upper_case_letters = $line =~ tr/A-Z//;
	#Skip lines that are more than half uppercase, which are mostly headings or table of contents mumbo-jumbo.
	if ($upper_case_letters/length($line) >= 0.5) {
	    if ($skip_mostly_uppercase) {
		$line = "";
	    }
	}
        #DROPPING OUT CAPITALIZED LINES ELIMINATES A _LOT_ OF JUNK HEADERS. This is a judgment call, but does a heck of a lot of good on most OCR'ed text

	$line =~ s/-\s*[\n\r]//g; #hyphenated words at lineend shouldn't even have spaces between them.
	$line =~ s/[\n\r]/ /g; #remove newlines, replaces with spaces.
	$line =~ s/\t\f/ /g; #replace tabs and formfeeds with spaces--the awk counts on the text having NO TABS AT ALL.
	#And I'm reserving \f to myself to mark sentence breaks. Neither of these should have any meaning in scanned texts.
	$line =~ s/([\.\?!])(["'\)])/$2$1/g;
        #Move period to end of sentence
	$line =~ s/([\.\?!])(["'\)])/$2$1/g; #Move period to end of sentence again, in case there's double quotes or a period and parenthesis or something";
        $line =~ s/([\.!\?]) +/$1\f/g; #suffix sentence puncutation with formfeed--this is still bad with abbreviations, maybe I need a longer list of exceptions?
	$line =~ s/([\.!\?])$/$1\f/g; #Punctuation can come at the end of the line, too; but not in between characters.
	##COMMON ABBREVIATIONS NOT TO END SENTENCES ON: we're removing the formfeeds here.
	#needs to deal smarter with multiple consecutive things like this, but the /gi option is not working as it is supposed to.:
        $line =~ s/(\W)([A-Z]\.)\f/$1$2 /gi;
        $line =~ s/(\W)([A-Z]\.)\f/$1$2 /gi;
        $line =~ s/(\W)([A-Z]\.)\f/$1$2 /gi;
       	$line =~ s/\b(mr|ms|mrs|dr|prof|rev|rep|sen|st|sr|jr|ft|gen|adm|lt|col|etc)\.\f/ $1 \. /gi; #Abbreviations can start with a newline as well as a space.                        	
	#Here are some lines to remove the words "Digitized by Google" even when it scans poorly.
	if ($use_goog_switch) {
	    $line =~ s/^.*digitize?d?.? by.*$//gi;                       
	    $line =~ s/^.*([vli]j|[gq])oo[gqs] ?[il1][ce].*$//gi; #kill any lines that have Google-matching keywords in them.
	    $line =~ s/^.*googl.*$//gi; #kill any lines that have Google-matching keywords in them.
	}
	$line =~ s/([ \f!\?@%^*\(\)\[\]\-=\{\}\|\\:;<>,\/~`"#\+])/ $1 /g; #Surround punctuators with spaces`
	$line =~ s/'([^s])/ ' $1/gi; #single quotes aren't word separators when part of possessive,but otherwise are
	$line =~ s/'([^s])/ ' $1/gi; #Need to do it twice for some reason.
	$line =~ s/\$([^\d])/ \$ $1/gi; #dollar signs aren't separators when preceding numerals.
	$line =~ s/([^\d])\.([^\d])/$1 \. $2/gi; #Periods aren't separators when part of decimal numbers.
	$line =~ s/\.$/ \./gi;# (Make sure to space out periods at end of line
	#Hashes aren't separators when following a-g,j or x
	$line =~ s/(\W[^a-gjx])#/$1 #/gi;

	$line =~ s/  +/ /g; #Replace multiple spaces with a single space
	$line =~ s/ ?\f ?/\n/g; #put newlines at the end of sentences, and strip surrounding spaces

	if ($line =~ m/(\n[^\n]*)$/) {
	    #Plus one for the newline
	    $currentlength = length($1);
	} else {
	    $currentlength += length($line);
	}

	if ($currentlength>64000) {
	    #the awk component fails if this is too long.
	    #Just break at the top of the line if so.
	    $line= "\n" . $line;
	    $currentlength = length($line);
	    if ($currentlength > 64000) {
		#breaks it every 32,000 characters (which may split a word or two, making this a kludge) until it's down to size.
		$line =~ s/([^\n]{1,32764})/$1\n/gs;
	    }
	}
	print "$line";
    }

    #the words "google.com" comes at the end of the Google Intro page; this catches it even when it's poorly ocr'ed.
    if ($line =~ m/[gq]oo[gq][li1]e\W*com/gi) {$googswitch = 1;}# $switchedat = $linenumber; print "Switching:\t"}

}
