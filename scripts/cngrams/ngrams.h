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

#ifndef _Ngrams_h
#define _Ngrams_h

#include "INgrams.h"
#include "ternarySearchTree.h"
#include "config.h"

/**
* class for common ngram operations
* Revisions:
* Feb 18, 2006. Jerry Yu
* Initial implementation
*/

class Ngrams : public INgrams
{
public:

	Ngrams( int newNgramN, const char * newInFileName, const char * newOutFileName, const char * newDelimiters = Config::getDefaultDelimiters(), const char * newStopChars = Config::getDefaultStopChars() );

	~Ngrams()
	{
		releaseQueue();
		delete[] totals;
		delete[] uniques;
	}

	/**
	* feed a token in, the token will be processed internally to generating ngram
	*
	* for word ngram, the token will be word string, 
	* for character ngram, the token will be a string of the character.
	*/

	virtual void addToken ( const string & token );

	/**
	* set delimiters
	*/
	void setDelimiters( const char * newDelimiters )
	{
		this->delimiters = newDelimiters ;
	}

	void setStopChars( const char * newStopChars )
	{
		this->stopChars = newStopChars;
	}

	string & getInFileName()
	{
		return this->inFileName;
	}

	int getN()
	{
		return ngramN;
	}

	/**
	* This methods return true if given char is set to be a delimiter
	* @param c - input character
	* @return true if c is set to be a delimiter
	*/
	bool isDelimiter( int c ) const  
	{ 
		return strchr( this->delimiters.c_str(), c ) != NULL;
	}

	/**
	* This methods return true if given char is set to be a stop char
	* @param c - input char
	* @return true if c is set to be a stop char
	*/
	bool isStopChar( int c ) const  
	{ 
		return strchr( this->stopChars.c_str(), c ) != NULL;
	}

	/**
	* total ngrams ( duplications are counted ), which is total of frequency of each ngram
	*/
	int total()
	{
		int ret = 0;
		for ( int i = 1; i<= ngramN; i++ )
		{
			ret += total( i );
		}
		return ret;
	}
	/**
	* total ngrams for given N of ngram( duplications are counted ), which is total of frequency of each ngram
	*/

	int total( int n )
	{
		return n > 0 && n <= ngramN ? totals [ n - 1 ] : 0;
	}

	/**
	* get total number of unique ngrams
	*/

	int count()
	{
		return ngramTable.count();
	}

	/**
	* get total number of unique ngrams for given N
	*/

	int count( int n )
	{
		return n > 0 && n <= ngramN ? uniques [ n - 1 ] : 0;

	}

protected:

	TernarySearchTree< NgramValue > ngramTable;
	string delimiters;

	struct TokenNode
	{
		string token;
		TokenNode * next;
		TokenNode ( const char * newToken ) : token( newToken ), next( 0 )
		{
		}
	};

	TokenNode * head, * tail;

	int ngramN;	// default number of ngrams

	/**
	* add a ngram to the ngram list.
	* if it is not on the list, add it, otherwise increase the ngram frequent count by 1
	* @param	n - number of the ngram
	*/

	void addNgram( const char * ngram, int n );

	/**
	* get all the items( key & value pairs ) in the tree
	* @param	n - n of ngram
	* @return	vector that contains all the item pointers
	*/

	Vector< TstItem<NgramValue> * > & getItems( )
	{
		return ngramTable.getItems();
	}

private:

	string inFileName;	// input text file name
	string outFileName;	// output text file name
	string stopChars;
	int tokenCount; //used for counting when parsing text
	int * totals;   // array for count total grams ( duplicated are counted ) for each N
	int * uniques; // array for counting unique grams for each each N

	/**
	* add token to the queue. The queue will be used to generate ngram
	* @param	token - token to be added to the queue.
	* @return	total number of tokens in the queue
	*/
	int pushQueue( const char * token );


	void popQueue();

	/**
	* Generate ngrams when queue has NGRAM_N - 1 tokens.
	* the token queue need to be processed specially for the first NGRAM_N - 1 tokens,
	* also need to be called if less than NGRAM_N tokens in the whole input text.
	* @param	count - total items in the queue
	*/
	virtual void preParse( int count )=0;

	/**
	* Once the queue is full, it will start to pop out ngrams
	* for each new token pushing in
	*/
	virtual void parse(){};

	// release queue memory
	void releaseQueue()
	{
		while ( tokenCount > 0 )
		{
			popQueue();
		}
	}
};

#endif
