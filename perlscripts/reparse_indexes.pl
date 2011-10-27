#!usr/bin/perl

my %wordids = load_in_list_of_words();
my %bookids = load_in_list_of_books();



for my $filename (keys %bookids) {
    reparse_book($filename,$bookids{$filename},%wordids)
}

sub reparse_book($filename,$bookid,%wordids) {
    
}
