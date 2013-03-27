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

#ifndef MY_STRING_H_
#define MY_STRING_H_

#include <iostream>
#include <assert.h>
#include <cstdlib>
#include <cstring>
#include <cstdio>

using namespace std;

#define string String

class StringIndexOutOfBounds { };

class string
{
public:

   // The size type used
   typedef unsigned int size_type;

   // string empty constructor
   string () : buffer(NULL), strLength(0), bufferLength(0) 
   {
   }

   // string constructors, mark them explicit to force us to find unnecessary casting
   //Construct a string from a null-terminated character array.
   //explicit 
   string( const char *cstring );     

   //Construct a string from a char
   //explicit 
   string( const char ch );

   //construct a string from an integer
   string ( int value ); 

   /**
    * Construct a string with char filled len times
    *
    * @param len length of new string.
    * @param char to fill the string.
    */
   string(size_t len, const char chr = ' ');

   /**
    * Construct a string with substring of str from index start with specified length 
    * @param str new string
    * @param start - start index
    * @param len - len of the substring
    */
   string( const string &str, size_t start, size_t len );

   /**
    * Copy constructor
    */
   string( const string & copy );
   
   /**
    * Destructor
    */
   virtual ~string( )
   { 
      if ( this->bufferLength )
         free( this->buffer );
      this->buffer =0;
      this->bufferLength = this->strLength =0;
   }

   // string  operators
   const string & operator = ( const char * content );
   const string & operator = ( const string & copy );
   const string & operator = ( const char ch );

   /*   bool operator == ( const string & str ) const;
   bool operator == ( const char* str ) const;
   bool operator != ( const string & str ) const;
   bool operator != ( const char* str ) const;
   bool operator < ( const string & str ) const;
   bool operator < ( const char* str ) const;
   bool operator > ( const string & str ) const;
   bool operator > ( const char* str ) const;
   bool operator <= ( const string & str ) const;
   bool operator <= ( const char* str ) const;
   bool operator >= ( const string & str ) const;
   bool operator >= ( const char* str ) const;
    */
   bool operator == ( const string & str ) const
   {
      return this->strLength == str.strLength && compare( str.c_str() ) == 0 ;
   }

   bool operator == ( const char * str ) const
   {
      return this->compare( str ) == 0 ;
   }

   bool operator!=( const string & str ) const
   {
      return this->strLength != str.strLength || !( *this == str );
   }

   bool operator!=( const char* str ) const
   {
      return !( *this == str );
   }

   bool operator < ( const string & str ) const
   {
      return this->compare( str.c_str() ) < 0 ;
   }

   bool operator < ( const char * str ) const
   {
      return this->compare( str ) < 0 ;
   }


   bool operator > ( const string & str ) const
   {
      return this->compare( str.c_str() ) > 0 ;
   }

   bool operator > ( const char * str ) const
   {
      return this->compare( str ) > 0 ;
   }

   bool operator <= ( const string & str ) const
   {
      return this->compare( str.c_str() ) <= 0 ;
   }

   bool operator <= ( const char * str ) const
   {
      return this->compare( str ) <= 0 ;
   }
   bool operator >= ( const string & str ) const
   {
      return this->compare( str.c_str() ) >= 0 ;
   }

   bool operator >= ( const char * str ) const
   {
      return this->compare( str ) >= 0 ;
   }

   // string += ( will use underline append operation )
   string & operator += ( const char * suffix )
   {
      assert( suffix );
      this->append ( suffix );
      return *this;
   }

   string & operator += ( int single )
   {
      this->append (single);
      return *this;
   }

   string& operator += ( const string & suffix )
   {
      this->append (suffix);
      return *this;
   }

   char   operator[]( unsigned k ) const; // Accessor operator[]
   char & operator[]( unsigned k );       // Mutator  operator[]

   /**  
    * Method to reserve a big amount of data when we know we'll need it. 
    * Be aware that this function clears the content of the dtring if any exists.
    */
   void reserve ( size_t size );

   /**
    * New size computation. It is simplistic right now : it returns twice the amount
    * we need
    */
   size_t assign_new_size (size_t minimum_to_allocate)
   {
      return minimum_to_allocate << 1;
   }

   /**
    * convert string into a classic char *
    */
   const char * c_str( ) const        
   {         
      return this->buffer;
   }

   /**
    * check whether string is empty
    */
   bool isEmpty () const
   {
      return this->length () ? false : true;
   }
   
   /**
    * Whether string is null
    *
    * @return true if is null.
    */
   inline bool operator!(void) const 
   { 
      return this->isNull(); 
   }

   /**
    * return true if the characters is NULL
    */
   bool isNull () const
   {
      return this->buffer ==  NULL;
   }

   // Return string length
   size_t length( ) const  
   { 
   	  return strLength ? strLength : 0; 
   }

   // Return string allocated size
   size_t getSize( ) const  
   { 
   	  return bufferLength ? bufferLength : 0; 
   }

   // single char extraction
   const char& at ( size_t index ) const
   {
      assert( index < this->length () );
      return this->buffer [index];
   }

   enum { MAX_LENGTH = 2048 };  // Maximum length for input string

   string & append ( const char *suffix ) 
   { 
      return this->append( suffix, strlen(suffix) ); 
   }

   string & append( const char* str, size_t len );

   // append function for another string
   string & append ( const string & suffix )
   {
      return this->append ( suffix.c_str (), suffix.length() );
   }

   // append for a single char.
   string & append(int c);

   /**
    * Insert c_string into a string.
    *
    * @param start starting offset to insert at.
    * @param cstring to insert
    */
   void insert(size_t start, const char *str);

   /**
    * Insert other string into a string.
    *
    * @param start string offset to insert at.
    * @param str string to insert.
    */
   void insert(size_t start, const string &str);

   /**
    * Insert c_string into a string.
    *
    * @param start starting offset to insert at.
    * @param cstring to insert
    * @param len length of the string
    */
   void insert(size_t start, const char *str, size_t len );

   /**
    * Retrieves a substring from this instance. 
    * The substring starts at a specified character position, and extracted to the end
    */
   inline string substring( size_t start ) const
   {
      return substring ( start, this->strLength );
   }

   /**
    * Return a new string that contains a specific substring of the
    * current string.
    *
    * @return new string.
    * @param start starting offset for extracted substring.   
    * @param len length of substring.
    */
   inline string substring( size_t start, size_t len) const 
   { 
      return string( *this, start, len ); 
   };

   /**
    * Returns a copy of this string in uppercase.
    * @return new string in upper case
    */

   string toUpper();

   /**
    * Returns a copy of this string in lower.
    * @return new string in lower case
    */

   string toLower();

   /**
    * Removes all space from both the start and end of this instance.
    */
   inline string & trim( )   
   { 
      return this->trim( " " );
   }

   /**
    * Removes all occurrences of a set of characters specified in an array from both the start and end of this instance.
    *
    * @param trimChars - An char to be removed or a null reference. 
    * @return The String that remains after all occurrences of the characters in trimChars are removed from both the  start and end.
    *         If trimChars is a null reference, white space characters are removed instead.
    */

   inline string & trim(const char *trimChars)
   {
      return this->trimEnd( trimChars ).trimStart( trimChars );
   }

   /**
    * Removes all space from the end of this instance.
    */
   inline string & trimEnd( )   
   { 
      return this->trimEnd( " " ); 
   }

   /**
    * Removes all occurrences of a set of characters specified in an array from the end of this instance.
    *
    * @param trimChars - An char to be removed or a null reference. 
    * @return The String that remains after all occurrences of the characters in trimChars are removed from the end.
    *         If trimChars is a null reference, white space characters are removed instead.
    */
   string & trimEnd( const char * trimChars );

   /**
    * Removes all space from the start of this instance.
    */
   inline string & trimStart( )   { return trimStart( " " ); }

   /** 
    * Removes all occurrences of a set of characters specified in an array from the beginning of this instance.
    *
    * @param trimChars - An char to be removed or a null reference. 
    * @return The String that remains after all occurrences of characters in trimChars are removed from the beginning. 
    *         If trimChars is a null reference, white space characters are removed instead.
    */
   string & trimStart( const char *trimChars );

   /**
    * Removes a specified number of characters from this instance beginning at a specified position.
    *
    * @param startIndex - The position in this instance to begin deleting characters.
    * @param count number of characters to erase.
    * @return current string instance less count number of characters.
    */
   void remove( size_t startIndex, size_t count );

   string & replace ( const char * oldValue, const char * newValue )
   {
      if ( oldValue && newValue )
      {
         int index = 0;
         while ( ( index = indexOf( oldValue, index ) ) != -1 )
         {
            replace ( index, strlen( oldValue ), newValue );
            index++;
         }
      }
      return *this;
   }


   /**
    * Replace text at a specific position in the string with new
    * text.
    *
    * @param startIndex -  starting offset to replace at.
    * @param len - length of text to remove.
    * @param text - text to replace with.
    * @param count - size of replacement text.
    */
   string & replace(size_t startIndex, size_t len, const char *text, size_t count );

   /**
    * Replace text at a specific position in the string with new
    * string,
    *
    * @param startIndex starting offset to replace at.
    * @param len length of text to remove.
    * @param replStr string to replace with.
    */
   string & replace( size_t startIndex, size_t len, const string &replStr );


   /**
    * get total number of occurrence of chars that appears in the string
    * @param chars - pattern string
    * @return total number of occurrence
    */
   int getOccurrence( const char * chars ) const;


   /**
    * Reports the index of the first occurrence of a String with length len, or one or more characters, within this instance.
    * @param chars - NULL terminated char string
    * @return The index position of value if that character is found, or -1 if it is not.
    */
   int indexOf( const string& str ) const { return indexOf( str.c_str() ); }

   /**
    * Reports the index of the first occurrence of a String with length len, or one or more characters, within this instance.
    * @param chars - NULL terminated char string
    * @return The index position of value if that character is found, or -1 if it is not.
    */
   int indexOf( const char * chars ) const { return chars ? indexOf( chars, 0 ) : -1; }

   /**
    * Reports the index of the first occurrence of a String with length len, or one or more characters, within this instance.
    * @param chars - NULL terminated char string
    * @param startIndex - start position of the string for searching
    * @return The index position of value if that character is found, or -1 if it is not.
    */
   int indexOf( const char * chars, size_t startIndex ) const  { return indexOf( chars, startIndex, chars? strlen(chars) : 0 ); }

   /**
    * Reports the index of the first occurrence of a String with length len, or one or more characters, within this instance.
    * @param chars - NULL terminated char string
    * @param startIndex - The search starting position.
    * @param len - length of the string for search
    * @return The index position of value if that character is found, or -1 if it is not.
    */
   int indexOf( const char * chars, size_t startIndex, size_t len ) const ;

   /**
    * String Pattern Match with Boyer-Moore algorithm, which is 
    * considered as the most efficient algorithm in usual applications.
    *
    * @param pattern - NULL terminated pattern string ( can also be called keyword )
    * @param len - length of the pattern string
    * @param startIndex - the start position of the string for searching.
    * @return The index position of value if pattern string is found, or -1 if it is not.
    */
   int BoyerMooreSearch( const char * str, const char* pattern, size_t len ) const;

   /**
    * Re-allocate buffer space for string.
    * resize methods changes the size of the string buffer to the given size. 
    * size can be any size, larger or smaller than the original. 
    * If len is zero, then the string becomes a null string.
    *
    * @param size new size to use.
    * @example 
    * str = "Hello world";
    * str.resize(6);
    * // str == "Hello"
    * str.resize(80);
    * // str == "Hello"
    */

   void resize(size_t newSize );

   // Releases the memory that not used by string, to save memory.
   void squeeze ();
   /**
    * whether the string is a number
    */
   bool isNumber() const
   {
      bool ret = true;
      for ( unsigned i=0; i<this->strLength; i++)
      {
         if ( !isdigit( (unsigned char)buffer[i] ) )
         {
            ret = false;
            break;
         }
      }
      return ret;
   }

   /**
    * Reset the string to an empty string.
    */
   void empty ()
   {
      if ( this->bufferLength )
      {
         this->buffer[0] = 0;
         this->strLength = 0;
      }
   }

private:
   char *buffer;                  // storage for characters
   size_t strLength;                 // length of string (# of characters)
   size_t bufferLength;              // capacity of buffer
   // Internal function that clears the content of a string
   void emptyIt ()
   {
      if ( this->bufferLength )
      {
         free( this->buffer );
      }
      this->init();
   }



   /**
    * Internal function that initialize the string object
    */
   void init();

   /**
    * A derivable low level comparison operator.  This can be used
    * to create custom comparison data types in derived string
    * classes.
    *
    * @return 0 if match, or value for ordering.
    * @param text text to compare.
    * @param len length of text to compare.
    * @param index offset from start of string, used in searchs.
    */
   inline int compare(const char *text, size_t len = 0, size_t index = 0) const
   {
      if(!text)
      {
         text = "";
      }
      return index > this->strLength ? -1 : len ? strncmp( this->buffer + index, text, len) : strcmp( this->buffer + index, text);
   }

};

ostream & operator<<( ostream & out, const string & str );    // Output
istream & operator>>( istream & in, string & str );           // Input
istream & getline( istream & in, string & str );              // Read line

string operator + ( const string &s1, const char c2 );
string operator + ( const char c1, const string &s2);
string operator + ( const string &s1, const string &s2 );
string operator + ( const string &s1, const char *s2 );
string operator + ( const char *s1, const string &s2 );
string operator + ( const string & s1, const char* s2 );
string operator + (const char* s1, const string & s2);

#endif
