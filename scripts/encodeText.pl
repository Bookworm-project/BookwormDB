#!/usr/bin/perl

use strict;

###
# This program takes command line input: first, the type of parsing ('bigrams','ungirams',etc)
# and second, a list of files to translate (which can, in testing be up to about 250,000 items long.)
# Just passsed through the arguments list, that seems like the easiest way to handle control flow.
# The primary goal here is minimize the number of times we have to load in that hash of words, which takes
# several seconds, by letting it get used on several different items.
#
# It uses perl instead of python for speed.
###
my $parsingType = shift @ARGV;

#These values aren't actually used anywhere now: there's just for checking validity.
my %wordlengths;
$wordlengths{'unigrams'} = 1;
$wordlengths{'bigrams'} = 2;
$wordlengths{'trigrams'} = 3;
$wordlengths{'quadgrams'} = 4;

die "Must enter valid parsing type ('unigrams','bigrams',etc.)" 
    unless (exists($wordlengths{$parsingType}));

my @filesToParse = @ARGV;

open(DICT,'files/texts/wordlist/wordlist.txt');

my %wordid;

my $i = 1;
while (my $dictEntry = <DICT>) {
    my @splat = split(/\t/,$dictEntry);
    $wordid{$splat[1]} = $splat[0];
}

for my $file(@filesToParse) {
    my $output = "files/texts/encoded/$parsingType/$file.txt";
    my $input = "files/texts/$parsingType/$file.txt";
    unless (-e $output) {
	if (-e $input) {
	    print "$output being written to\n";
	    open(INPUT,$input);
	    open(OUTPUT,">$output");
	    while (<INPUT>) {
		my @splat = split(/ /,$_);
		my $count = pop @splat;
		my @return;
		for my $word (@splat) {
		    my $wordcode = $wordid{$word};
		    push(@return,$wordcode);
		}
		unless (undef~~@return || '' ~~ @return) {
		    print OUTPUT join("\t",@return) . "\t" . $count;
		} 
	    }
	} else {print "$input does not exist, skipping\n"}
    } else { print "$output already exists, skipping\n";}
}
