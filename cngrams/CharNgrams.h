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

#ifndef _CHAR_NGRAMS_H_
#define _CHAR_NGRAMS_H_

#include "ngrams.h"

/**
* this class implements all character ngram related operations
* Revisions:
* Feb 18, 2006. Jerry Yu
* Initial implementation
*/

class CharNgrams : public Ngrams
{

public:

	CharNgrams( int newNgramN, const char * newInFileName, const char * newOutFileName, const char * newDelimiters = Config::getDefaultDelimiters(), const char * newStopChars = Config::getDefaultStopChars() );

	virtual ~CharNgrams();

	void addTokens();

	/**
	* sort ngrams by frequency/ngram/or both, then output
	*/

	void output();

private:

	/**
	* Generate ngrams when queue has NGRAM_N - 1 tokens.
	* the token queue need to be processed specially for the first NGRAM_N - 1 tokens,
	* also need to be called if less than NGRAM_N tokens in the whole input text.
	* @param	count - total items in the queue
	*/
	void preParse( int count );

	/**
	* Once the queue is full, it will start to pop out ngrams
	* for each new token pushing in
	*/

	void parse();

	/**
	* get all ngrams for given N
	* @return total number of ngrams for the N
	*/
	void getNgrams( vector< NgramToken * > & ngramVector, int n );

};
#endif
