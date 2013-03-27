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

#ifndef VECTOR_H
#define VECTOR_H

#define vector Vector

#include <stdio.h>
#include <assert.h>

class ArrayIndexOutOfBoundsException { };

template <class Object>
class vector
{
   /*enum {   GROW_THRESHOLD = 8388608, // threshold to grow by block size, otherwise simplely double current memory size.
      GROW_BLOCK_SIZE = 4194304
   };
   */

private:
   size_t currentSize; /* current number of items in the vector */
   size_t maxSize;   /* max number of items the vector can hold */
   Object * objects; /* pointer to the actual memory holding objects */
   /**
    * static callback function for sorting, the objects should be sorted in ascending order, from lowest value to highest value.
    */
   static int compareObjectsAsc( const void* a, const void* b ) 
   {
      Object * x = (Object*)a;
      Object * y = (Object*)b;
      return *x < *y ? -1 : *x == *y ? 0 : 1;
      /*if( *x < *y ) return -1;
      else if( *x == *y ) return 0;
      else return 1;
      */
   }
#if 0
   /**
    * static callback function for sorting, the objects should be sorted in descending order, from highest value to lowest value.
    */
   static int compareObjectsDesc( const void* a, const void* b ) 
   {
      Object * x = (Object*)a;
      Object * y = (Object*)b;
      return *x > *y ? -1 : *x == *y ? 0 : 1;
      /*
      if( *x > *y ) return -1;
      else if( *x == *y ) return 0;
      else return 1; */
   }
#endif

public:

   /**
    * vector constructor
    * input: size of vector to be constructed. if not specified, default to 0
    */
   explicit vector( unsigned newMaxSize = 0 ) : currentSize( 0 ), maxSize( newMaxSize )
   { 
      objects = maxSize > 0 ? new Object[ maxSize ] : 0;
   }

   /**
    * vector destructor
    */
   ~vector( )
   {
      this->clear();
   }

   /**
    * vector copy
    */
   vector( const vector & v ) : objects( 0 )
   { 
      operator=( v ); 
   }

   /**
    * returns the number of items in the vector
    */
   size_t count( ) const
   { 
      return currentSize; 
   }

   /**
    * Gets the number of elements that the vector can contain.
    */
   size_t capacity() const
   {
      return maxSize;
   }

   /**
    * Removes all elements from the vector
    */
   void clear();

   /**
    * Inserts an element into the vector at the specified index.
    */
   void insert( const Object &val, size_t pos );

   /**
    *    Adds an object to the end of the vector
    */
   void add( const Object &val );

   /**
    * Removes the element at the specified index of the vector.
    */
   void  removeAt( unsigned index );

   /**
    * Removes a range of elements from the vector.
    * 
    * @param index - The zero-based starting index of the range of elements to remove.
    * @param count - The number of elements to remove.
    */
   void removeRange( unsigned index, unsigned count );

   /**
    * Removes the first occurrence of a specific object from the vector.
    * This method performs a linear search; therefore, the average execution time is 
    * proportional to Count. That is, this method is an O(n) operation, where n is Count.
    */
   void remove ( const Object &val );

   /**
    * Tests if the specified object is a component in this vector.
    *
    * @param val - an object.
    * @return true if the vector contains the element, otherwise false
    */
   bool contains ( const Object &val );

   /**
    * The member function inserts an element with value val at the end of the controlled sequence.
    */
   void push_back(const Object& val);

   /**
    * operator[] which get the index-th element in the vector
    * 
    * @param index - element index
    * @return the index-th element
    */
   Object & operator[]( unsigned index ) const
   {
      /*if( index < 0 || index >= currentSize )
      {
         throw ArrayIndexOutOfBoundsException( );
      }
      */
      assert( index < currentSize );
      return objects[ index ];
   }

   /**
    * Returns the element at the specified position in this Vector.
    *
    * @param index - index of element to return.
    * @return object at the specified index
    */
   Object & get( unsigned index ) const
   {
      return this->operator []( index );
   }

   /**
    * Replaces the element at the specified position 
    * in this Vector with the specified element.
    * 
    * @param index - index of the vector element  that will be replaced
    * @param element - the element that will replace existing one on the vector
    * @return the element previously at the specified position.
    * 
    */
   Object set( unsigned index, const Object & element );

   /**
    * Searches for the first occurence of the given argument, beginning the search at index, and testing for equality using the equals method.
    *
    * @param val - the object to be searched
    * @return the index of the first occurrence of the object argument 
    *         in this vector
    *         returns -1 if the object is not found. 
    *         (Returns -1 if index >= the current size of this Vector.)
    */
   int indexOf( Object val );

   /**
    * Searches for the first occurence of the given argument, beginning the search at index, and testing for equality using the equals method.
    *
    * @param val - the object to be searched
    * @param index - the non-negative index to start searching from.
    * @return the index of the first occurrence of the object argument 
    *         in this vector at position index or later in the vector, 
    *         that is, the smallest value k such that 
    *         elem.equals(elementData[k]) && (k >= index) is true; 
    *         returns -1 if the object is not found. 
    *         (Returns -1 if index >= the current size of this Vector.)
    */
   int indexOf( Object val, unsigned index );

   /**
    * Returns the index of the last occurrence of the specified object in this vector.
    * 
    * @param val - the desired component.
    * @return the index of the last occurrence of the specified object 
    *         in this vector, that is, the largest value k such that 
    *         elem.equals(elementData[k]) is true; returns -1 if the object is not found.
    */
   int lastIndexOf( const Object & val );

   /**
    * Searches backwards for the specified object, 
    * starting from the specified index, and returns an index to it.
    * 
    * @param val - the desired component.
    * @param index - the index to start searching from.
    * @return   the index of the last occurrence of the specified 
    *         object in this vector at position less than or equal 
    *          to index in the vector, that is, the largest value k 
    *          such that elem.equals(elementData[k]) && (k <= index) is true; 
    *          -1 if the object is not found. (Returns -1 if index is negative.)
    */
   int lastIndexOf( const Object & val, unsigned index );

   /**
    * Fuction to compare two itemss
    * @return
    * - negative, if item 1 at address itemAddr1 less than item 2 at address itemAddr2.
    * - zero, equal
    * - positive, if item 1 > item 2nction
    */
   typedef int (*CompareFunction)( const void *itemAddr1, const void *itemAddr);

   /**
    * This method uses uses the QuickSort algorithm. 
    * This is an O(n ^2) operation, where n is the number of elements to sort, 
    * with an average of theta(n log n).
    * sortAsc will sort objects in ascending order
    * sortDes will sort objects in descending order
    */
   
   /*enum { SORT_ASC, SORT_DESC };
   void sort() { sort( SORT_ASC); }
   void sort ( int sortOrder )
   {
      qsort( objects, currentSize, sizeof(Object), sortOrder == SORT_ASC ? vector<Object>::compareObjectsAsc : vector<Object>::compareObjectsDesc );
   }
   void sortAsc() { sort( SORT_ASC ); }
   void sortDesc() { sort( SORT_DESC ); }
    */
   
   /**
    * sort items in the vector by given compare function
    * if compare function is not specefied, default to Vecotr::compareObjectsAsc
    */
   void sort( CompareFunction compareFunction = compareObjectsAsc ) 
   {   
      qsort( objects, currentSize, sizeof(Object), compareFunction );
   }

   /**
    * Reverses the order of the elements in the entire vector.
    */
   void reverse();

   /**
    * Reverses the order of the elements in the specified range.
    * 
    * @param index - The zero-based starting index of the range to reverse.
    * @param count - The number of elements in the range to reverse. 
    */
   void reverse( unsigned index, unsigned count );

   /**
    * assign operator
    */
   const vector & operator = ( const vector & v );

   /**
    * resize the internal array to newSize.
    * If newSize less than current array size, vector array will not be changed.
    */
   void resize( unsigned newSize );

};

template <class Object>
const vector<Object> & vector<Object>::operator=( const vector<Object> & v )
{
   if( this != &v )
   {
      if( maxSize > 0 )
      {
         delete [ ] objects;
      }
      maxSize = v.capacity();
      currentSize = v.count();
      if ( maxSize )
      {
         objects = new Object[ maxSize ];
      }
      for( unsigned k = 0; k < currentSize; k++ )
      {
         objects[ k ] = v.objects[ k ];
      }   
   }
   return *this;
}

template <class Object>
void vector<Object>::resize( unsigned newSize )
{
   Object *oldArray = objects;
   if ( newSize < currentSize )
   {
      currentSize = newSize;
   }
   objects = new Object[ newSize ];
   for( unsigned k = 0; k < currentSize; k++ )
   {
      objects[ k ] = oldArray[ k ];
   }

   if( maxSize > 0 )
   {
      delete [ ] oldArray;
   }
   maxSize = newSize;
}

template <class Object>
void Vector<Object>::insert( const Object &val, size_t pos )
{
   size_t originalMaxSize = maxSize;

   //if (pos < 0 || pos > currentSize)
   //   throw ArrayIndexOutOfBoundsException( );
   assert ( pos >= 0 && pos <= currentSize );

   if ( currentSize == maxSize ) 
   {
      maxSize = maxSize != 0 ? maxSize << 1 : 1;
      /*if ( maxSize < GROW_THRESHOLD )
         maxSize *= 2;
      else
         maxSize += GROW_BLOCK_SIZE;
      if ( maxSize <= 0 )
         maxSize = 1;
      */
      Object *newObjects = new Object[maxSize];
      
      for ( unsigned i = 0; i < currentSize; i++ )
         newObjects[i] = objects[i];
      
      if ( originalMaxSize>0 )
      {
         delete[] objects;
      }
      
      objects = newObjects;

   }
   for ( size_t i = currentSize; i > pos; i-- )
      objects[i] = objects[i-1];
   objects[pos] = val;
   ++currentSize;
}


template <class Object>
inline void vector<Object>::push_back( const Object& val )
{
   this->insert( val, currentSize );
}

template <class Object>
void vector<Object>::clear()
{
   if( maxSize > 0 )
   {
      delete [ ] objects;
   }
   currentSize = maxSize = 0;
}

template <class Object>
inline void vector<Object>::add( const Object &val )
{
   this->insert( val, currentSize );
}

template <class Object>
void vector<Object>::removeAt( unsigned index )
{
   removeRange( index, 1 );
}

template <class Object>
void vector<Object>::removeRange( unsigned index, unsigned count )
{
   /*if ( index < 0 || index + count > currentSize ) // index out of boundary
      throw ArrayIndexOutOfBoundsException( );
    */
   assert( index >= 0 && index + count <= currentSize );

   for ( unsigned i = index; i < currentSize-1; i++ )
   {
      objects[i] = objects[i+count];
   }

   currentSize -= count;
}

template <class Object>
void vector<Object>::remove (const Object &val)
{
   for ( unsigned i=0; i<currentSize; i++ )
   {
      if ( objects[i] == val )
      {
         removeAt( i ); // if find the first occurrence, remove it.
         break;
      }
   }
}

template <class Object>
bool vector<Object>::contains ( const Object &val )
{
   bool ret = false;
   for ( unsigned i=0; i<currentSize; i++ )
   {
      if ( objects[i] == val )
      {
         ret = true;
         break;
      }
   }
   return ret;
}
template <class Object>
Object vector<Object>::set( unsigned index, const Object & element )
{
   /*if( index < 0 || index >= currentSize )
   {
      throw ArrayIndexOutOfBoundsException( );
   }
    */
   assert( index >= 0 && index < currentSize );
   Object original( this->operator []( index ) );
   this->operator []( index ) = element;
   return original;
}

template <class Object>
int vector<Object>::indexOf( Object val)
{
   return indexOf( val, 0 );
}



template <class Object>
int vector<Object>::indexOf( Object val, unsigned index )
{
   int ret = -1;
   /*if ( index < 0 || index >= currentSize )
   {
      throw ArrayIndexOutOfBoundsException( );
   }*/
   assert( index >= 0 && index < currentSize );
   for ( unsigned i=index; i<currentSize; i++ )
   {
      if ( objects[i] == val )
      {
         ret = ( int ) i;
         break;
      }   
   }
   return ret;
}


template <class Object>
int vector<Object>::lastIndexOf( const Object & val )
{
   return currentSize > 0 ? lastIndexOf( val, (int)currentSize - 1 ) : -1;
}

template <class Object>
int vector<Object>::lastIndexOf( const Object & val, unsigned index )
{
   int ret = -1;
   /*if ( index < 0 || index >= currentSize )
   {
      throw ArrayIndexOutOfBoundsException( );
   }
    */
   assert( index >= 0 && index < currentSize );
   for ( int i=index; i>=0; i -- )
   {
      if ( objects[i] == val )
      {
         ret = ( int ) i;
         break;
      }   
   }
   return ret;
}

template <class Object>
void vector<Object>::reverse( )
{
   if ( currentSize > 0 )
   {
      reverse( 0, (unsigned ) currentSize );
   }
}

template <class Object>
void vector<Object>::reverse( unsigned index, unsigned count )
{
   /*if ( index < 0 || index >= currentSize || count <= 0 || count > currentSize )
   {
      throw ArrayIndexOutOfBoundsException();
   }
    */
   assert( index >=0 && index < currentSize && count > 0 && count <= currentSize );
   unsigned midIndex = ( index+count ) / 2;
   unsigned endIndex = index + count -1;

   for ( unsigned i = 0; i<midIndex; i++ )
   {
      Object tmp = objects[i];
      objects[ i ] = objects[ endIndex - i ];
      objects[ endIndex - i] = tmp;
   }
}

#endif
