#!usr/bin/perl
use DBI;
use feature qw(switch say state);
use strict;
use warnings;
use DBI;
#use Term::ProgressBar 2.00;
use feature qw(switch say state);




sub check_if_table_exists {
	my $sql_tablename = shift();
	my $dbh = get_dbh();
	my $querystring = '
		SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
		WHERE TABLE_NAME = "' . $sql_tablename .'";';
	my $sth = $dbh->prepare($querystring); $sth -> execute();
	my $exists; while (my @row = $sth->fetchrow_array()) {$exists = "$row[0]";}
	$exists;
}

sub iadownload {
    	my $iacode = shift;
		open (OUTPUT,">/Volumes/Rameau's Nephew/IAtexts/Downloads/$iacode.txt");
		#say "Getting http://www.archive.org/download/$iacode/$iacode"."_djvu.txt";
		print OUTPUT get("http://www.archive.org/download/$iacode/$iacode"."_djvu.txt");
		close (OUTPUT);
}

sub fisher_yates_shuffle {
	my $deck = shift;  # $deck is a reference to an array
	my $i = @$deck;
	while ($i--) {
		my $j = int rand ($i+1);
		@$deck[$i,$j] = @$deck[$j,$i];
	}
}

sub load_permitted_words {
	my %permitted;
	my $dbh = get_dbh();
	my $sth = $dbh->prepare("select word from words WHERE wordid <200000");
	$sth->execute();
	while(my @row = $sth->fetchrow_array) {
		$permitted{$row[0]} = 1;
	}
	return %permitted;
}

sub load_relevant_bookids {
	#takes a query term and an array of values
	my ($where_term,$index,@results) = @_; # THIS SHOULD WORK IF IT INCLUDES WHERE AT THE FRONT
	my $dbh = get_dbh();
	my $querystring = "SELECT " . $index . "," . join("," , @results) . " from catalog $where_term;";
	my $sth = $dbh -> prepare ($querystring);
	$sth->execute();
	my %hash;

	while(my @row = $sth->fetchrow_array) {
		for my $i (1..$#results) {
			$hash{$row[0]}{$results[$i-1]} = $row[$i];
		}
	}
	return %hash;
	
}

sub insert_query {
	my ($tablename, $fieldnames, @queryarray) = @_;
	my $dbh = get_dbh();
	unless ($#queryarray == -1) {
		my $querystring = "insert into " . $tablename . " ($fieldnames) " . "	
		VALUES\n" . join("",@queryarray);
		$querystring =~ s/,\n$/;/gi;	# Fix the last line
		#say $querystring;
		my $sth = $dbh->prepare("$querystring");
		$sth->execute();
	}
}

sub create_local_bookcounts_table {
	#NB THIS ALSO CREATES THE OTHER THREE WORDCOUNT TABLES, THE YEAR ONE AND THE SUPPLEMENT ONE
	my ($keyword, $catalog_subset) = @_;
	my $dbh = get_dbh();
	my $sql_tablename = sqlname($keyword,"bookcounts", $catalog_subset);
	my $exists = check_if_table_exists($sql_tablename);
	if ($exists==0) {
		say "Creating new Table $sql_tablename...";
		my $querystring = "CREATE TABLE " . $sql_tablename . " (
			id INT UNSIGNED NOT NULL AUTO_INCREMENT,
			bookid VARCHAR(29),
			word VARCHAR(20),
			count INT UNSIGNED,
			PRIMARY KEY (id)
		);";
		my $sth = $dbh->prepare($querystring); $sth -> execute();
		create_local_occurrences_table($keyword,$catalog_subset);
		if ($keyword eq " ") {
        	create_bookcounts_appendix ($catalog_subset);
    	}
    
	}
	if ($exists==1) 
		{die "Better delete the previous versions of these tables first to avoid duplicates\n"}
}

sub create_bookcounts_appendix {
	my $catalog_subset = shift();
	my $dbh = get_dbh();
	my $querystring = "CREATE TABLE bookcounts_appendix_" . $catalog_subset . " (
		bookid VARCHAR(29), INDEX bookid (bookid,word(18),count),
		word VARCHAR(255), INDEX word (word(18),bookid,count),
		count INT,
		PRIMARY KEY (bookid, word,count)
	);";
	my $sth = $dbh->prepare($querystring); $sth -> execute();	
	#This should probably check if the table is already there.
}

sub fix_up_indexes {
	my ($keyword, $catalog_subset) = @_;
	my $dbh = get_dbh();
	my $bookcountsname = sqlname($keyword,"bookcounts", $catalog_subset);
	my $occtabname	   = sqlname($keyword,"occurrences_table", $catalog_subset);
	say "Adding indexes and analyzing tables (This may take a day or two)";
	my @queries = ("ALTER TABLE $bookcountsname
		ADD INDEX wordext (word,bookid,count),
		ADD INDEX bookext (bookid,word,count);",
		"ALTER TABLE $occtabname
		ADD INDEX wordext (word,year,count);",	
		"ANALYZE TABLE $bookcountsname;",
		"ANALYZE TABLE $occtabname;");
	for my $querystring (@queries) {
			say $querystring;
			my $sth = $dbh->prepare($querystring); $sth -> execute();
		}
		
}

sub create_local_occurrences_table {
	my $dbh = get_dbh();
	my ($keyword, $catalog_subset) = @_;
	my $sql_tablename = sqlname($keyword,"occurrences_table",$catalog_subset);
	say "Creating new Table $sql_tablename...";
	my $querystring = "CREATE TABLE " . $sql_tablename . " (
			year SMALLINT,
			word VARCHAR(20),
			count INT UNSIGNED,
			bookcount MEDIUMINT UNSIGNED,
			PRIMARY KEY (year,word,count)
		);";
	my $sth = $dbh->prepare($querystring); $sth -> execute();
}

sub sqlname {
	my($keyword,$tabletype,$catalog_subset) = @_;
	my $sql_tablename = "$tabletype $catalog_subset " .$keyword;
	$sql_tablename =~ s/ /_/gi;
	$sql_tablename =~ s/_*$//gi;
	return($sql_tablename);
}

sub get_dbh { 
	my $dbh = DBI->connect("dbi:mysql:presidio", "mayor", "newton") or die "Database connection failed\n";
	$dbh;
}

1;
