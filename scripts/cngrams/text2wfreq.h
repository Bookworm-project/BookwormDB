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

#ifndef text2wfreq_h
#define text2wfreq_h

#include "WordNgrams.h"
#include "CharNgrams.h"

/**
* This class utilizes WordNgrams and CharNgrams classes to generate and output ngrams.
* Revisions:
* Feb 18, 2006. Jerry Yu
* Initial implementation
*/

class Text2wfreq
{
public:

	/**
	* Constructor
	*/

	Text2wfreq()
	{
		ngramN = Config::DEFAULT_NGRAM_N;
		ngramType = Config::DEFAULT_NGRAM_TYPE;
		inFileName = "";
		outFileName = "";
	}

	~Text2wfreq()
	{
	}


	/**
	* get options
	*/
	bool getOptions( int argc, char * argv[] );

	/**
	* display help information 
	*/
	void showHelp();

	void printOptions ()
	{
		printf ( "ngramN %d, ngramType %s, inFileName %s, outFileName %s.\n", ngramN, ngramType == Config::CHAR_NGRAM?"character":"word", inFileName.c_str(), outFileName.c_str() );
	}


	int getNgramN() 
	{
		return ngramN;
	}

	int getNgramType()
	{
		return ngramType;
	}

	string getInFileName()
	{
		return inFileName;
	}

	string getOutFileName()
	{
		return outFileName;
	}

private:
	int ngramN;	// default number of ngrams
	int ngramType;	// default type
	string inFileName;	// input text file name
	string outFileName;	// output text file name

};

#endif
