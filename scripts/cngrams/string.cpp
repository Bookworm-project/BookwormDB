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

#include "mystring.h"

#define D(x)
#define MAX(a,b) a>b ? a : b;
string::string( const char * cstring )
{
   assert ( cstring );
   if ( cstring )
   {
   	  this->bufferLength = ( this->strLength = strlen( cstring ) ) + 1;
   	  if ( ( this->buffer = ( char * ) malloc( this->bufferLength ) ) )
   	  {
           memcpy ( this->buffer, cstring, this->bufferLength );
   	  }
   	  else
   	  {
   	     this->init();
   	  }
   }
   else
   {
      this->init();
   }
}

string::string( const char ch ) : strLength(1), bufferLength(2)
{
   if ( ( this->buffer = ( char * ) calloc( 2, 1 ) ) )
   {
      this->buffer[0]= ch;
   }
}

string::string ( int value ) 
{
   char valueBuffer[32];
   sprintf( valueBuffer, "%d", value );
   this->strLength = strlen( valueBuffer );
   this->resize( this->strLength + 1 );
   memcpy( this->buffer, valueBuffer, this->bufferLength ); 
}

string::string( size_t len, const char chr )
{
   this->resize( len + 1);
   memset( this->buffer, chr, len);
   this->strLength = len;
}

string::string( const string & copy ) 
{
   if ( copy.bufferLength )
   {
      this->bufferLength = ( this->strLength = copy.strLength ) + 1;
      if ( ( this->buffer = (char*) malloc( this->bufferLength ) ) )
      {
         memcpy ( this->buffer, copy.buffer, this->bufferLength );
      }
      else
      {
         this->init();
      }
   }
   else
   {
      this->init(); // initialize the string object
   }

}

string::string( const string &str, size_t start, size_t len )
{
   assert ( start <= str.length() );
   // if given length is overpass the size of string, use the longest substring available.
   size_t count = str.length() - start;
   if ( len <= count )
   {
      count = len;
   }
   this->bufferLength = ( this->strLength = ( str.length() - start ) ) + 1;
   if ( len < this->bufferLength )
   {
      this->bufferLength = ( this->strLength = len ) + 1;
   }
   this->buffer = ( char* ) malloc( this->bufferLength );
   memcpy ( this->buffer, str.c_str() + start, this->strLength );
   buffer[ this->strLength ] =0;
}


// string = operator. Safe when assign own content
const string & string::operator = ( const char * content )
{
   if ( content )
   {
      this->strLength = strlen (content);
      if ( !this->bufferLength )
      {
         this->bufferLength = this->strLength + 1;
         this->buffer = ( char * ) malloc( this->bufferLength );
      }
      else if ( this->bufferLength <= this->strLength )
      {
         this->bufferLength = this->strLength + 1;
         this->buffer = ( char * ) realloc( this->buffer, this->bufferLength );
      }
      memcpy ( this->buffer, content, this->strLength + 1 );
   }
   else
   {
      this->emptyIt ();
   }
   return *this;
}

const string & string::operator=( const string & copy )
{
   // Prevent copy to self! if copy itself, do nothing.
   if ( &copy != this ) 
   {
      this->strLength = copy.strLength;
      if ( !this->bufferLength )
      {
         this->bufferLength = this->strLength + 1;
         this->buffer = ( char * ) malloc( this->bufferLength );
      }
      else if ( this->bufferLength <= this->strLength )
      {
         this->bufferLength = this->strLength + 1;
         this->buffer = ( char * ) realloc( this->buffer, this->bufferLength );
      }
      memcpy ( this->buffer, copy.buffer, this->strLength + 1 );
   }
   return *this;
}


const string & string::operator=( const char ch )
{
   this->emptyIt();

   this->bufferLength = 2;
   if ( ( this->buffer = (char*) calloc( this->bufferLength, 1 ) ) )
   {
      this->buffer[0] = ch;
      this->strLength = 1;
   }
   else
   {
      this->init();
   }
   return *this;
}

string operator + ( const string & s1, const string & s2 )
{
   return s1 + s2.c_str();
}
string operator + ( const string & s1, const char* s2 )
{
   return string( s1 ) += s2;
}

string operator + (const char * s1, const string & s2)
{
   return string( s1 ) += s2;
}

string operator + ( const string &s1, const char c2 )
{
   return string( s1 ) += c2;
}

inline string operator + ( const char c1, const string &s2)
{

   return string ( c1 ) += s2;
}

// append a const char * to an existing string
string & string::append( const char* str, size_t len )
{
   if (str)
   {
      size_t previousLength = this->length();
      
      if (len + previousLength >= this->bufferLength)
      {
         this->resize (len + previousLength + 1);
      }
      
      if (this->buffer)
      {
         memcpy (this->buffer + previousLength, str, len); 
         
         this->strLength += len;
         
         this->buffer [this->strLength] = '\0';
      }
   }     
   return *this;
}

inline string & string::append(int c)
{
   size_t len = this->length();
   if( len + 1 >= this->getSize() )
      this->resize(len + 2);

   this->buffer[len++] = (char)c;
   this->strLength =len;
   this->buffer[len] = 0;
   return *this;
}



char & string::operator[ ]( unsigned k )
{
   assert( k < strLength );
   return this->buffer[ k ];
}

char string::operator[ ]( unsigned k ) const
{
   assert ( k < strLength );
   return this->buffer[ k ];
}

ostream & operator<<( ostream & out, const string & str )
{
   return out << str.c_str();
}

istream & operator>>( istream & in, string & str )
{
   char buf[ string::MAX_LENGTH + 1 ];
   in >> buf;
   if( !in.fail( ) )
      str = buf;
   return in;
}

istream & getline( istream & in, string & str )
{
   char buf[ string::MAX_LENGTH + 1 ];
   in.getline( buf, string::MAX_LENGTH );
   if( !in.fail( ) )
      str = buf;
   return in;
}

void string::reserve ( size_t size )
{
   this->emptyIt ();
   if (size)
   {
      if ( ( this->buffer = (char*)malloc( size ) ) )
      {
         this->bufferLength = size;
         this->buffer [0] = 0;
         this->strLength = 0;
      }
   }
}

void string::resize(size_t newSize )
{
   newSize = newSize > 0 ? newSize : 0;
   if ( ( this->buffer = ( char* )realloc( buffer, newSize ) ) )
   {
      this->buffer[ this->strLength ] = 0;
      this->bufferLength = newSize;
   }
   else
   {
      this->init();
   }
}

void string::squeeze ()
{
   this->resize( strLength +1 );
}

inline void string::init()
{
   this->buffer = NULL;
   this->bufferLength = this->strLength = 0;
}

inline void string::insert( size_t start, const char *str )
{
   this->insert( start, str, strlen( str ) );
}

inline void string::insert( size_t start, const string &str )
{
   this->insert( start, str.c_str(), str.length() );
}

void string::insert( size_t start, const char *str, size_t len )
{


   if( !str || len<=0 || start < 0 || start > this->strLength  )
      return;

   if( this->strLength + len +1 >= this->bufferLength )
   {
      resize( strLength + len + 1);
   }

   memmove( this->buffer + start + len, this->buffer + start, this->strLength - start );
   memmove( this->buffer + start, str, len );
   this->strLength += len;
   return;
}   

string string::toUpper()
{
   string newString( *this );
   if ( !newString.isNull() && !newString.isEmpty() )
   {
      char* ptr = newString.buffer;
      do 
      {
         *ptr = (char) toupper( *ptr );
      }
      while ( *ptr++ );
   }
   return newString;
}

string string::toLower()
{
   string newString( *this );
   if ( !newString.isNull() && !newString.isEmpty() )
   {
      char* ptr = newString.buffer;
      do 
      {
         *ptr = (char) tolower( *ptr );
      }
      while ( *ptr++ );
   }
   return newString;
}

string & string::trimEnd( const char * trimChars )
{
   if ( !trimChars )
      trimChars = " ";

   size_t len = strlen( trimChars );

   if ( !this->isNull() && !this->isEmpty() )
   {
      if ( len <= this->strLength )
      {
         if ( 0 == memcmp( this->buffer + this->strLength - len, trimChars, len ) )
         {
            this->strLength -= len;
            this->buffer[ strLength ] =0;
         }
      }
   }
   return *this;
}

string & string::trimStart( const char *trimChars )
{

   if ( !trimChars )
      trimChars = " ";

   size_t len = strlen( trimChars );

   if ( !this->isNull() && !this->isEmpty() )
   {
      if ( len <= this->strLength )
      {
         if ( 0 == memcmp( this->buffer, trimChars, len ) )
         {
            memmove( this->buffer, this->buffer + len, this->strLength - len );
            this->strLength -= len;
            this->buffer[ this->strLength ] = 0;
         }
      }
   }
   return *this;
}

void string::remove( size_t startIndex, size_t count )
{
   if ( startIndex >= this->strLength )
      return;

   if ( startIndex + count >= this->strLength || ! count )
   {
      this->strLength = startIndex;
      this->buffer [ this->strLength ] = 0;
      return;
   }      

   memmove( this->buffer + startIndex, this->buffer + startIndex + count, this->strLength - startIndex - count );
   this->strLength -= count;
   this->buffer[ this->strLength ] = 0;
}

string & string::replace ( size_t startIndex, size_t len, const char *replChars, size_t count )
{
   remove( startIndex, len);
   this->insert( startIndex, replChars, count );
   return *this;
}

string & string::replace(size_t startIndex, size_t len, const string &replStr)
{
   remove( startIndex, len );
   this->insert( startIndex, replStr );
   return *this;
}

/* Brute Force implementation of string pattern matching*/
/*
int string::indexOf( const char * chars, size_t startIndex, size_t len ) const
{
int ret = -1;
int index = 0;
if( chars && startIndex < strLength )
{
while( len + index <= strLength )
{
if( compare( chars + startIndex, len, index ) == 0)
return index;
++index;
}
}
return ret;
}
*/
int string::getOccurrence( const char * chars ) const
{
   int count = 0, index = 0;
   while ( ( index = this->indexOf( chars, (size_t)index )  ) != -1 )
   {
      ++index;
      ++count;
   }
   return count;
}

int string::indexOf( const char * chars, size_t startIndex, size_t len ) const
{
   int index = -1;
   if( chars && startIndex < this->strLength && len <= this->strLength )
   {
      index = this->BoyerMooreSearch( this->buffer + startIndex, chars, len );
   }
   return index == -1 ? -1 :  index + (int)startIndex;
}

int string::BoyerMooreSearch( const char * str, const char* pattern, size_t len ) const
{
   const int max_chars = 256; // max number of unique chars
   int skip[ max_chars ];

   for( int i=0; i<max_chars; ++i )  skip[i] = (int)len;
   for( int i=0; i<(int)len; ++i ) skip[ (unsigned char)pattern[i] ] = (int)len - i - 1;

   int textIndex, patternIndex, intLen = (int)strlen( str );
   for( textIndex = patternIndex = (int)len-1; patternIndex >= 0; --textIndex, --patternIndex )
   {
      while( str[textIndex] != pattern[patternIndex] ) 
      {
         textIndex += MAX( (int)len - patternIndex, skip[ (int)str[textIndex] ] ); // reposition the text index
         if( textIndex >= intLen ) 
         {
            return -1; // pattern string not found in text string.
         }
         patternIndex = (int)len-1; // repoint to last char of pattern string
      }
   }
   return textIndex + 1;
}
