/*******************************************************************
C++ Package of  Ternary Search Tree
Copyright (C) 2006  Zheyuan Yu

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

Read full GPL at http://www.gnu.org/copyleft/gpl.html

Email me at jerryy@gmail.com if you have any question or comment
WebSite: http://www.cs.dal.ca/~zyu

*************************************************************************/
#include "text2wfreq.h"
#include <iostream>
#include <time.h>

using namespace std;

bool Text2wfreq::getOptions( int argc, char * argv[] )
{

	if ( argc < 2 )
	{
		return false;
	}

	if ( Config::hasOption( "--help", argc, argv ) || Config::hasOption( "-help", argc, argv ) )
	{
		return false;
	}

	string value = Config::getOptionValue( "-type", argc, argv );

	if ( value == "character" )
	{
		ngramType = Config::CHAR_NGRAM;
	}
	else if ( value == "word" )
	{
		ngramType = Config::WORD_NGRAM; 
	}
	else if ( value != "" )
	{
		printf( "wrong type option!\n" );
		return false;
	}

	value = Config::getOptionValue( "-n", argc, argv );

	if ( value != "" )
	{
		sscanf( value.c_str(), "%d", &ngramN );
	}

	inFileName = Config::getOptionValue( "-in", argc, argv );
	outFileName = Config::getOptionValue( "-out", argc, argv );

	return true;
}

/**
* display help information 
*/
void Text2wfreq::showHelp()
{
	printf( "\nUsage: ngrams [options]\n" );
	printf( "Compute all the word/char frequencies for the given text file.\n" );
	printf( "Options:\n" );
	printf( "--n=N			Number of ngrams, the default is %d-grams.\n", Config::DEFAULT_NGRAM_N );
	printf( "--type=T		character or word, the default is %s.\n",(int) Config::DEFAULT_NGRAM_TYPE == (int)Config::WORD_NGRAM ? "word" : "character" );
	printf( "--in=training files	default to stdin.\n");
	printf( "--out=output file	default to stdout. ( currently stdout only )\n\n");

}

int main( int argc, char * argv[] )
{
	time_t startTime;
	time( &startTime );
	Text2wfreq tf;

	if ( tf.getOptions( argc, argv ) )
	{
		//tf.printOptions();
	}
	else
	{
		tf.showHelp();
		return 0;
	}
	INgrams * ngrams;
	if ( tf.getNgramType() == Config::WORD_NGRAM )
	{	// word ngrams
		ngrams = new WordNgrams( tf.getNgramN(), tf.getInFileName().c_str(), tf.getOutFileName().c_str() );
	}
	else	// char ngrams
	{
		ngrams = new CharNgrams( tf.getNgramN(), tf.getInFileName().c_str(), tf.getOutFileName().c_str() );
	}

	time_t midTime;
	time( &midTime );
	// fprintf( stderr, "ngrams have been generated, start outputing.\n" );
	ngrams->output();
	if ( ngrams )
	{
		delete ngrams;
		ngrams = NULL;
	}
	time_t endTime;
	time( &endTime );

	// fprintf( stderr, "\nSubtotal: %ld seconds for generating ngrams.\n", midTime-startTime );
	// fprintf( stderr, "Subtotal: %ld seconds for outputing ngrams.\n", endTime-midTime );
	// fprintf( stderr, "Total %ld seconds.\n", endTime-startTime );




}
