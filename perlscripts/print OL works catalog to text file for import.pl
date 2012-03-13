#! usr/bin/perl
use strict;
use warnings;
no warnings 'utf8';
use JSON;
use feature qw(switch say state);
use Data::Dumper;

my $data_directory = shift;
my $ol_dump_name = shift;
my $project_directory = shift;
require "$project_directory/perlscripts/python calls.pl";


print_OL_editions_catalog_to_text_file($data_directory . "/Catinfo/" . $ol_dump_name);

sub print_OL_editions_catalog_to_text_file {
    my $open_library_catalog = shift;
    my %bookdata; my %oclcs; my %lccns; my %checkworks;
    my %fields = (
	"ocaid" => "string",
	"title" => "string",
	"publish_country" => "string",
	"publish_date" => "string",    
	"lc_classifications" => "array",
	"oclc_numbers" => "array",
	"lccn" => "array",
	"publish_places" => "array",
	"publishers" => "array",
	"languages" => "hash", #hash inside array leading to key, as following
	"key" => "string",
	"authors" => "hash",
	"works" => "hash",
	"is_a_duplicate" => "string",
	"lc1" => "string",
	"lc2" => "string"
	);
    
    my @fieldnames = ("ocaid" ,
		      "title" ,
		      "publish_country" ,
		      "publish_date" ,    
		      "lc_classifications" ,
		      "oclc_numbers" ,
		      "lccn" ,
		      "publish_places" ,
		      "publishers" ,
		      "languages" ,
		      "key" ,
		      "authors" ,
		      "works"
	);
    
    open (FH, $open_library_catalog) or die "Error in opening catalog: $!\n";
    
    my $kept = 0;
    
    open (FIRSTVALUES, ">$data_directory/Edition Data.txt");
    open (ADDITIONALVALUES, ">$data_directory/Additional Edition Data.txt");
    open (LCSH, ">$data_directory/LCSH.txt");
    while(<FH>) {
	my @parts = split("\t",$_);
	my $ref = decode_json $parts[4];
	my %hash = %{$ref}; 
	# If requirements that it have a file, some identifier that connects to other catalogs OR a catalog number, and a publish date
	if (exists($hash{"ocaid"})) { #has to be goog friendly, temp removed
	    my $id = $hash{"ocaid"};
	    if ( exists( $hash{"publish_date"} ) && $hash{"publish_date"} =~ m/(\d\d\d\d$)/) {
		$hash{"publish_date"} = $1;
	        if (exists ($hash{"subjects"})) {
		    my @subjects = @{$hash{"subjects"}};
		    for my $subject (@subjects) {
			$subject =~ s/\.$//gi;
			my @splitted = split(" -- ",$subject);
			print LCSH fix_extra_slashes($hash{"key"}) . "\t";
			for my $splittum (@splitted) {
			    print LCSH "$splittum\t";
			}
			print LCSH "\n"
		    }
		}
		foreach my $field (@fieldnames) {
		    if ($fields{$field} eq "string") {# The Strings we just print straight out
			my $string = "";
			if (defined($hash{$field})) {
			    $string = $hash{$field};
			    $string = fix_extra_slashes($string);
			}
			print FIRSTVALUES "$string\t";
		    }
		    if ($fields{$field} eq "array") {#The arrays we print the first element, then cat all
			# subsequent ones to another file with the book identifier. 
			# It's not perfect, but I'm putting a 
			# premium on being able to parse the first bit of info.
			my $string = "";
			if (exists($hash{$field})) {
			    my @localarray = @{$hash{$field}};
			    $string = $localarray[0];
			    if ($#localarray >= 1) {
				for my $value (@localarray[1..$#localarray]) {
				    print ADDITIONALVALUES $hash{"key"}."\t$field\t$value\n";
				}
			    }
			}
			print FIRSTVALUES "$string\t";
		    }
		    if ($fields{$field} eq "hash") { # The we treat as the arrays, using the values stored under "key"             
			my $string = "";
			if (exists($hash{$field})) {
			    my @localarray = @{$hash{$field}};
			    $string = $localarray[0]{"key"};
			    if ($#localarray >= 1) {
				for my $value (@localarray[1..$#localarray]) {
				    my %lochash = %{$value};
				    my $string2 = fix_extra_slashes($lochash{"key"});
				    print ADDITIONALVALUES $hash{"key"}."\t$field\t." . $string2 . "\n";
				}
			    }
			}
			$string = fix_extra_slashes($string);
			print FIRSTVALUES "$string\t";
		    }
		}
		print FIRSTVALUES "\n";   
	    }
	}
    }
}



sub fix_extra_slashes { 
    my $string = shift();
    $string =~ s/\/authors\///gi;
    $string =~ s/\/books\///gi;
    $string =~ s/\/languages\///gi;
    $string =~ s/\/works\///gi;
    $string;
}

