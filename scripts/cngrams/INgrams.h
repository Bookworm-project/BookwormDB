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

#ifndef _INGRAMS_H_
#define _INGRAMS_H_
#include "mystring.h"
/**
* Define the interface for ngram classes
* Revisions:
* Feb 18, 2006. Jerry Yu
* Initial implementation
*/
class INgrams
{
public:
	struct NgramValue
	{
		int n; // N of ngram
		int frequency; 
		NgramValue () : n(0), frequency(0)
		{
		}
		NgramValue ( int newN, int newFrequency ) : n( newN ), frequency( newFrequency )
		{
		}
	};

	struct NgramToken 
	{
		NgramToken()
		{
		}
		NgramToken( string & newNgram, NgramValue & newValue )
		{
			ngram = newNgram;
			value = newValue;
		}
		// Copy constructor
		NgramToken( const NgramToken & copy )
		{
			ngram = copy.ngram;
			value = copy.value;
		}
		string ngram;
		NgramValue value;

		void operator=( const NgramToken & ngramToken )
		{
			ngram = ngramToken.ngram;
			value = ngramToken.value;
		}
		/**
		* use following operators if we need to order the ngrams by frequency
		*/
		bool operator>( const NgramToken & ngramToken ) const
		{
			return value.frequency > ngramToken.value.frequency;
		}
		bool operator>=( const NgramToken & ngramToken ) const
		{
			return value.frequency >= ngramToken.value.frequency;
		}
		bool operator==( const NgramToken & ngramToken ) const
		{
			return value.frequency == ngramToken.value.frequency;
		}
		bool operator<( const NgramToken & ngramToken ) const
		{
			return value.frequency < ngramToken.value.frequency;
		}		
		bool operator<=( const NgramToken & ngramToken ) const
		{
			return value.frequency <= ngramToken.value.frequency;
		}
		/**
		* use following operators if we need to order the ngrams by ngram
		*/
		/*
		bool operator>( const NgramToken & ngramToken ) const
		{
		return ngram < ngramToken.ngram;
		}
		bool operator>=( const NgramToken & ngramToken ) const
		{
		return ngram >= ngramToken.ngram;
		}
		bool operator==( const NgramToken & ngramToken ) const
		{
		return ngram == ngramToken.ngram;
		}
		bool operator<( const NgramToken & ngramToken ) const
		{
		return ngram < ngramToken.ngram;
		}		
		bool operator<=( const NgramToken & ngramToken ) const
		{
		return ngram <= ngramToken.ngram;
		}
		*/

		/**
		* use following operators if we need to order the ngrams by frequency and ngram 
		*/
		/*
		bool operator>( const NgramToken & ngramToken ) const
		{
		return value.frequency > ngramToken.value.frequency || value.frequency == ngramToken.value.frequency && ngram < ngramToken.ngram ;
		}
		bool operator>=( const NgramToken & ngramToken ) const
		{
		return value.frequency >= ngramToken.value.frequency || value.frequency == ngramToken.value.frequency && ngram <= ngramToken.ngram;
		}
		bool operator==( const NgramToken & ngramToken ) const
		{
		return value.frequency == ngramToken.value.frequency && ngram == ngramToken.ngram;
		}
		bool operator<( const NgramToken & ngramToken ) const
		{
		return value.frequency < ngramToken.value.frequency || value.frequency == ngramToken.value.frequency && ngram > ngramToken.ngram;
		}		
		bool operator<=( const NgramToken & ngramToken ) const
		{
		return value.frequency <= ngramToken.value.frequency || value.frequency == ngramToken.value.frequency && ngram > ngramToken.ngram;
		}	
		*/
	};

	/**
	 * compare function to compare two NgramToken pointers
	 * - negative, if item 1 at address itemAddr1 less than item 2 at address itemAddr2.
	 * - zero, equal
	 * - positive, if item 1 > item 2nction
	 */
#if 0
	static int compareFunction (const void * a, const void * b)		/* sort by alphabet */
	{
		/*printf("comparing %s - %s.\n", ((Element*)a)->key, ((Element*)b)->key ); */
		return strcmp( ( ( *( NgramToken** )a ) )->ngram.c_str(), ( *( ( NgramToken** )b ) )->ngram.c_str() );
		/*String * x = *( ( String ** ) a );
		String * y = *( ( String ** ) b );
        return *x > *y ? 1 : *x == *y ? 0 : -1;
		*/
	}
#endif
	static int compareFunction (const void * a, const void * b)		/* sort by frequency and word */
	{
		int freq1 = ( *( ( NgramToken ** ) a ) )->value.frequency;
		int freq2 = ( *( ( NgramToken ** ) b ) )->value.frequency;
        return freq1 > freq2 ? -1 : freq1 == freq2 ? strcmp( ( ( *( NgramToken** )a ) )->ngram.c_str(), ( *( ( NgramToken** )b ) )->ngram.c_str() ) : 1;
		
	}
	/**
	* constructor
	*/
	INgrams( );

	/**
	* destructor
	*/
	virtual ~INgrams();

	/**
	* feed a token in, the token will be processed internally to generating ngram
	*
	* for word ngram, the token will be word string, 
	* for character ngram, the token will be a string of the character.
	*/

	virtual void addToken ( const string & token )=0;

	/**
	* sort ngrams by frequency/ngram/or both, then output
	*/
	virtual void output() =0 ;

	virtual	void setDelimiters( const char * newDelimiters )=0;

	/**
	* get total number of ngrams
	*/
	virtual int count()=0;

	/**
	* get total number ngrams for given N
	*/
	virtual int count( int n )=0;

};


#endif
