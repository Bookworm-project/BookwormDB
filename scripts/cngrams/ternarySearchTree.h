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

/*
* File: ternarySearchTree.h
* ----------------
* This file declare TernarySearchTree class.
*
* Ternary search tree stores keys in sorted order, which can be used as a symbol table.
* 
* Searching operation is lightning fast, it is reported usually comparable with hashing table, 
* and substantially faster than hashing for unsuccessful searches.
*
* Ternary search tree gracefully grows and shrinks, unlike hash table which usually use
* an array and need to be rebuilt after large size changes.
*
* Advance operations such as traversal to get sorted item list, partial matching 
* and near-neighbor search are supported natively.
*
* Ternary search tree is initially proposed by Jon Bentley and Bob Sedgewick.
* see references: 
* Fast Algorithms for Sorting and Searching Strings: http://www.cs.princeton.edu/~rs/strings/paper.pdf
* Ternary Search Trees: http://www.ddj.com/documents/s=921/ddj9804a/9804a.htm
*
* Revisions:
*
* Jan 16, 2006. Zheyuan Yu.
* Initial creation of ternary search tree class
*
*/

#ifndef _TernarySearchTree_h
#define _TernarySearchTree_h

// uncomment following define to display tree infomation
//#define TST_INFO_ENABLE

#include "vector.h"
#include "mystring.h"

/**
* define tree node structure
*/

typedef struct TstNode * TstTree;

typedef struct TstNode 
{
	TstNode( char c ) : splitChar(c), left(0), right(0), mid(0)
	{
	}
	char splitChar;
	TstTree left, right;
	union {
		TstTree mid;
		int index;
	};
} tstNode;

/**
* structure to hold key/value pair, used when building balanced tree.
*/

template <class Object>
struct TstItem
{
	TstItem ( const string & newKey, const Object & newValue ) : key( newKey ), value( newValue)
	{
	}

	TstItem()
	{
	}

	~TstItem()
	{
	}

	string key;
	Object value;
	
	void operator=( const TstItem & item )
	{
		key = item.key;
		value = item.value;
	}
	bool operator>( const TstItem & item ) const
	{
		return key > item.key;
	}
	bool operator==( const TstItem & item ) const
	{
		return key == item.key;
	}
	bool operator<( const TstItem & item ) const
	{
		return key < item.key;
	}

};
template <class Object>
class TernarySearchTree 
{

public:

	/**
	* Class constructor
	*/

	TernarySearchTree ();

	/**
	* Class destructor
	*/

	~TernarySearchTree ();


	/**
	* Build balanced tree by binary inserting item of a sorted item list.
	* 
	* @param	itemVector - vectors that holds all item which is pair of key & value
	* Note: current TST tree will be cleared before build balanced tree.
	*
	*/

	void buildBalancedTree( Vector< TstItem<Object> > & itemVector );

	/**
	* Determines whether the Ternary Search Tree contains a specific key.
	* 
	* @param	key - The key to locate in the tree.
	* @return	true if the tree contains an element with the specified key; otherwise, false.
	*/

	bool contains( const char * key );

	/**
	* get item with the specified key from the tree
	* 
	* @param	key - The key to locate in the tree
	* @return	pointer to the item, NULL if key not found
	*/

	inline TstItem<Object> * getItem( const char * key )
	{
		int index = this->getItemIndex( key );
		return index == -1 ? NULL : itemVector[ index ];
	}

	/**
	* get item from the tree at specified position
	* 
	* @param	index - The index of the item in the item vector
	* @return	pointer to the item, NULL if not found
	*/
	
	inline TstItem<Object> * getItem( int index )
	{
		assert( index >= 0 && index < itemCount );
		return itemVector[ index ];
	}

	inline Vector< TstItem<Object> * > & getItems( )
	{
		return itemVector;
	}

	/**
	* Get key from the tree
	*
	* @param	index - The index of the item in the key vector.
	* @return	The key of the item with specified index, NULL if not found
	*/

	inline const char * getKey( int index )
	{
		return index == -1 ? NULL : itemVector[ index ]->key.c_str();
	}

	/**
	* get value with the specified key from the tree
	* 
	* @param	key - The key to locate in the tree
	* @return	pointer to the value, NULL if key not found
	*/

	inline Object * getValue( const char * key )
	{
		int index = this->getItemIndex( key );
		return index == -1 ? NULL : &( itemVector[ index ]->value );
	}

	/**
	* get value from the tree
	* 
	* @param	index - The index of the value in the value vector
	* @return	pointer to the value, NULL if not found
	*/

	Object * getValue( int index )
	{
		return index == -1 ? NULL : &( itemVector[ index ]->value );
	}

	/**
	* Search to find the index of the specified key in the key vector
	* inline to improve search performance.
	*
	* @param	key - key to be search in the ternary search tree
	* @return	index of the key in key vector. If key is not found, return -1
	*/

	int getItemIndex( const char * key )
	{
		int index = -1; /* index of the key in keyVector */
		int diff, sc = *key;
		TstTree p = root;

		while (p) 
		{
			if ((diff = sc - p->splitChar) == 0) 
			{
				if (sc == 0) // found the key
				{
					index = p->index; // get the index of the key
					break;
				}
				sc = *++key;
				p = p->mid;
			} 
			else if (diff < 0)
				p = p->left;
			else 
				p = p->right;
		}
		// if index -1, that means the search has run off the end of the tree, the key not found
		return index;
	}

	/**
	* This method executes a partial-match searching.
	* .o.o.o matches the single word rococo, while the pattern
	* .a.a.a matches many words, including banana, casaba, and pajama.
	* Tal* matches all word with prefix Tal
	* @param	key - pattern for the searching
	* @return	an index vector for all returned keys
	*/

	Vector<int> partialMatchSearch( const char * key );

	/**
	* Search near neighbors that are withing a given Hamming distance of the key.
	*
	* @param	key	- key to be searched
	* @param	distance - Hamming distance for the search.
	* @return	an index vector for all matching keys
	*
	* @example search for jerry with distance 1 will return berry, ferry, gerry and etc.
	*
	*/

	Vector<int> nearSearch( const char * key, int distance )
	{
		Vector<int> nearVector;
		nearVectorPtr = &nearVector;
		nearSearch( root, key, distance );
		return nearVector;
	}
	/**
	* This method return all keys that has the given prefix.
	* 
	* @param	prefix - prefix to search keys
	* @return	an index vector for all returned keys
	*
	* Note: character '?' will match any char, 
	* '*' will match any char(s), which can only be used as last char in the pattern for current implementation.
	*/

	Vector<int> prefixSearch( const char * prefix )
	{
		//string str( prefix );
		//str.append('*');
		return partialMatchSearch( string( prefix ).append('*').c_str() );
	}

	/**
	* print the strings in the tree in sorted order with a recursive traversal
	*/

	Vector<int> getSortedItemIndexes( );


	/**
	* Adds an element with the specified key and value into the ternary search tree
	*
	* @key	key of the element to be inserted into the tree
	* @value value of the element to be inserted into the tree
	*/

	TstNode * add( const char * key, const Object & value );

	/**
	* Get total number of key & value pair in the tree
	*/

	int count() const 
	{
		return itemCount;
	}

	/**
	* Clean up the tree, nodes and stored values will all released
	*/

	void clear()
	{ 
#ifdef TST_INFO_ENABLE
		nodeCount=0;
#endif
		// clean up the tree
		cleanup( root ); 
		// clean up key, value vectors and reset variables.
		/*keyVector.clear();
		valueVector.clear();
		*/
		/* release memory of items */
		for ( int i = 0; i < itemCount; i++ )
		{
			delete itemVector[i];
		}
		itemVector.clear();
		root = NULL;
		itemCount = 0;
		existingItemIndex = -1;
#ifdef TST_INFO_ENABLE
		fprintf( stderr, "total %d node in the TST tree, node size %d, total %d bytes.\n", nodeCount, 13, nodeCount * 13 );
		fprintf( stderr, "total %d bytes for strings.\n", strLenCount );
#endif
	}

private:

	/**
	* Add a key into the ternary search tree
	* 
	* @key	key to be inserted
	* @return the leaf node of the key( node with splitChar == 0 )
	*/

	TstNode * add( const char* key );
#ifdef TST_INFO_ENABLE
	int nodeCount, strLenCount;
#endif

	/**
	* clean up nodes in the tree. inline to improve performance
	*
	* @param p	root of the tree
	*/

	void cleanup( TstTree p )
	{   
		if (p) 
		{
#ifdef TST_INFO_ENABLE
			++nodeCount;
#endif
			cleanup(p->left);

			if (p->splitChar) 
			{
				cleanup(p->mid);
			}

			cleanup(p->right);
			delete(p);
		}
	}

	/**
	* Recursively search a pattern
	* ?o?o?o matches the single word rococo, while the pattern
	* ?a?a?a matches many words, including Canada, banana and casaba.
	* Tal* matches all word with prefix Tal
	*
	* @param	tree - root of the tree to be searched
	* @param	key - patterns for the search
	*/

	void partialMatchSearch( TstTree tree, const char * key );

	/**
	* Recursively search near neighbors that are withing a given Hamming distance of the key.
	*
	* @param	tree -	root of the tree to be searched
	* @param	key	- key to be searched
	* @param	distance - Hamming distance for the search.
	*
	* @example search for jerry with distance 1 will return berry, ferry, gerry and etc.
	*
	*/

	void nearSearch( TstTree tree, const char * key, int distance );

	/**
	* Recursively build balanced tree by binary inserting item of a sorted item list
	* from specified start to end position
	* 
	* @param	itemVector - vectors that holds all item which is pair of key & value
	* @param	start - start position of the vector
	* @param	end - end position of the vector
	* Note: current TST tree will be cleared before build balanced tree.
	*
	*/

	void buildBalancedTreeRecursive( Vector< TstItem<Object> > & itemVector, int start, int end );

	/**
	* Return a list of items sorted by key, by travering the tree recursively
	*/

	void getSortedItemIndexes( TstTree p );

	/*Vector<string> keyVector; // vector to track all inserted keys.

	Vector<Object> valueVector; // vector to track all inserted objects.
	*/
	Vector< TstItem<Object> * > itemVector; /* vector to track of inserted items */

	Vector<int> * sortedItemIndexVectorPtr;	// pointer to the vector of sorted items, used for recursive traverse

	Vector<int> * pmVectorPtr;	// pointer to the vector of partial matched items, used for recursive matching

	Vector<int> * nearVectorPtr; // pointer to the vector of near neighbor items, used for recursive searching.

	TstTree root;

	int itemCount;	// total number of items in the tree

	int existingItemIndex; // when inserting, if item already existed, it will be set the index of the existing item. If no existed, set to -1

};

template <class Object>
TernarySearchTree<Object>::TernarySearchTree ( ): 
sortedItemIndexVectorPtr(0), pmVectorPtr(0), nearVectorPtr(0), root(0), itemCount(0), existingItemIndex(-1)
{
#ifdef TST_INFO_ENABLE
	strLenCount=0;
#endif
}
template <class Object>
TernarySearchTree<Object>::~TernarySearchTree ( )
{
	this->clear();
}

template <class Object>
TstNode * TernarySearchTree<Object>::add( const char* key, const Object & value )
{
#ifdef TST_INFO_ENABLE
	strLenCount += sizeof( string(key)) + (int)strlen(key) + 1;
#endif
	TstNode * p = add( key );
	if ( p )
	{
		if ( this->existingItemIndex == -1 )
		{	// key not existed in tst tree
			this->itemVector.add( new TstItem<Object>( key, value ) );
			p->index = itemCount -1;
		}
		else
		{
			// if key alreay existed in the tree, replace its value with new value
			itemVector[ this->existingItemIndex ]->value = value;
			p->index = this->existingItemIndex;

		}
	}
	return p;
}

template <class Object>
TstNode* TernarySearchTree<Object>::add( const char* key )
{
	//cout<<"Inserting "<<key<<endl;
	TstTree p = this->root;
	TstTree parent = 0;
	if( key == 0 || *key == 0)
		return 0;

	while (p) {
		parent = p;
		if ( *key < p->splitChar )
		{
			p = p->left;
		}
		else if ( *key == p->splitChar )  
		{
			// return true, if the current character is the end-of-string character 0
			if ( *key == 0 )
			{
				this->existingItemIndex = p->index;
				break;
			}
			p = p->mid;
			++key;
		} 
		else
		{
			p = p->right;
		}
	}


	if( !p ) // key not found
	{
		this->existingItemIndex = -1;
		p = new TstNode( *key );
		//cout<<"char "<<p->splitChar<<endl;
		if ( parent )
		{

			/*if ( *key == parent->splitChar )
			{
				parent->mid = p;
			}
			else if ( *key < parent->splitChar )
			{ 
				parent->left = p;
			}
			else
			{
				parent->right = p;
			}
			*/
			int diff = *key - parent->splitChar;
			diff == 0 ? parent->mid = p : diff < 0 ? parent->left = p : parent->right = p;
			

		}
		if ( ! root )
		{
			root = p;
		}
		while ( p->splitChar )
		{
			++key;
			p->mid = new TstNode( *key );
			p = p->mid; // move to new node
		}

		++itemCount;
	}

	return p;
}

template <class Object>
bool TernarySearchTree<Object>::contains( const char * key )
{   
	return getItemIndex( key ) != -1;
}

template <class Object>
Vector<int> TernarySearchTree<Object>::getSortedItemIndexes( ) 
{
	Vector<int> sortedItemIndexVector;
	this->sortedItemIndexVectorPtr = &sortedItemIndexVector;
	this->getSortedItemIndexes( this->root );
	return sortedItemIndexVector;
}

template <class Object>
void TernarySearchTree<Object>::getSortedItemIndexes( TstTree p ) 
{   
	if ( p )
	{
		getSortedItemIndexes(p->left); 
		if (p->splitChar) 
		{
			getSortedItemIndexes(p->mid); 
		}
		else 
		{
			sortedItemIndexVectorPtr->add( p->index );
		}
		getSortedItemIndexes( p->right ); 
	}
}

template <class Object>
Vector<int> TernarySearchTree<Object>::partialMatchSearch( const char * key )
{
	Vector<int> pmVector;
	pmVectorPtr = &pmVector;
	partialMatchSearch( root, (char*)key );
	return pmVector;
}

template <class Object>
void TernarySearchTree<Object>::partialMatchSearch(TstTree tree, const char *key)
{
	if (!tree) return;

	// partial match left
	if (*key == '?' || *key == '*' || *key < tree->splitChar)
	{
		partialMatchSearch( tree->left, key );
	}
	// partial match middle
	if (*key == '?' || *key == '*' || *key == tree->splitChar)
	{
		if ( tree->splitChar && *key )
		{
			if ( *key == '*' )
			{
				partialMatchSearch( tree->mid, key );
			}
			else
			{
				partialMatchSearch( tree->mid, key+1 );	// search next pattern char
			}
		}
	}
	if ( ( *key == 0 ||  *key == '*' ) && tree->splitChar == 0 )
	{
		pmVectorPtr->add( tree->index );
	}

	if (*key == '?' || *key == '*' || *key > tree->splitChar)
	{
		partialMatchSearch( tree->right, key );
	}
}

template <class Object>
void TernarySearchTree<Object>::nearSearch( TstTree tree, const char * key, int distance )
{
	if ( !tree || distance < 0 ) 
	{
		return;
	}

	if ( distance > 0 || *key < tree->splitChar )
	{
		nearSearch( tree->left, key, distance );
	}

	if ( tree->splitChar == 0 )
	{
		if ( (int) strlen( key ) <= distance )
		{
			nearVectorPtr->add( tree->index );	// found the matched key, added it to index vector
		}
	}
	else
	{
		nearSearch( tree->mid, *key ? key+1 : key, ( *key == tree->splitChar ) ? distance : distance - 1 );
	}

	if ( distance > 0 || *key > tree->splitChar )
	{
		nearSearch( tree->right, key, distance );
	}
}
template <class Object>
void TernarySearchTree<Object>::buildBalancedTree( Vector< TstItem<Object> > & itemVector )
{
	int count = (int)itemVector.count();

	if ( count == itemVector.count() && count > 0 )
	{
		this->clear();
		// sort the items by keys, and binary insert, then we will get a balanced tree
		itemVector.sort();
		buildBalancedTreeRecursive( itemVector, 0, count - 1 );
	}
}

template <class Object>
void TernarySearchTree<Object>::buildBalancedTreeRecursive( Vector< TstItem<Object> > & itemVector, int start, int end )
{
	int mid;
	if ( start > end || end < 0 )
	{
		return;
	}
	mid = ( end - start + 1 ) / 2;
	add( itemVector[ start + mid ].key.c_str(), itemVector[ start + mid ].value );
	buildBalancedTreeRecursive( itemVector, start, start + mid - 1 );
	buildBalancedTreeRecursive( itemVector, start + mid + 1, end );
}

#endif
