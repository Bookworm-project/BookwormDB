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

#include "ngrams.h"

Ngrams::Ngrams( int newNgramN, const char * newInFileName, const char * newOutFileName, const char * newDelimiters, const char * newStopChars ) :
ngramN(newNgramN), inFileName(newInFileName), outFileName(newOutFileName)
{
	// initial queue
	head = tail = 0;
	tokenCount = 0;
	this->setDelimiters( newDelimiters );
	this->setStopChars( newStopChars );
	totals = new int[ ngramN ];
	uniques = new int[ ngramN ];
	memset( totals, 0, ngramN * sizeof(int) );
	memset( uniques, 0, ngramN * sizeof(int) );
}

void Ngrams::addToken ( const string & token )
{
	int count = this->pushQueue( token.c_str() );

	if ( count == this->ngramN )
	{
		this->parse();
		this->popQueue();
	} 
	else if ( count == this->ngramN - 1 )
	{
		this->preParse( count );
	} 

}

void Ngrams::addNgram( const char * ngram, int n )
{
	assert( n > 0 && n <= ngramN);
	NgramValue * value = ngramTable.getValue( ngram );

	if ( value ) // existing ngram, increase frequent count by 1
	{
		++ value->frequency;
	}
	else // new ngram, add it
	{
		ngramTable.add( ngram, NgramValue( n, 1 ) );
		++uniques[ n - 1 ];
	}
	++totals[ n - 1 ];
}

int Ngrams::pushQueue( const char * token )
{
	TokenNode * tokenNode = new TokenNode( token );
	if ( !head )
	{
		head = tokenNode;
	}
	else
	{
		this->tail->next = tokenNode;
	}
	this->tail = tokenNode;
	return ++tokenCount;
}

void Ngrams::popQueue()
{
	if ( head )
	{
		if ( head == tail )
		{
			tail = 0;
		}
		TokenNode * p = head->next;
		delete head;
		head = p;
		--tokenCount;
	}
}
