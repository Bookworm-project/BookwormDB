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

/**
* define contants that used by the package
* Revisions:
* 1.0 Feb 3, 2006. Jerry Yu
* Initial creation
*
*/

#ifndef NGRAM_CONFIG_H
#define NGRAM_CONFIG_H

#include "mystring.h"

class Config
{
public:
	enum 
	{ 
		WORD_NGRAM,		// word ngram
		CHAR_NGRAM		// char ngram
	};

	enum 
	{
		DEFAULT_NGRAM_TYPE = WORD_NGRAM		// default ngram type
	};

	enum
	{
		DEFAULT_NGRAM_N = 3
	};


	/**
	* get the default delimiters
	*/

	static const char * getDefaultDelimiters()
	{
		return " \t,.?;<>'\"`~!+-*/@#$%^&(){}[]|=\\:‘“”—";
	}

	/**
	* get the default delimiters
	*/

	static const char * getDefaultStopChars()
	{
		return " \n\r";
	}


	/**
	* get the value of an argument in a command line
	*
	* @param	option - name of the argument
	* @param	argc - total number of argument
	* @param	argv - argument list
	* @return	value of the option. If not found, return ""
	*/

	static string getOptionValue ( string option, int argc, char * argv[] )
	{
		string value = "";
		string commandLine = "";
		for ( int i = 0; i < argc; i++ )
		{
			commandLine += " ";
			commandLine += string( argv[i] );
		}
		int start = commandLine.toLower().indexOf ( option.toLower() );
		if ( start != -1 )
		{
			value = commandLine.substring( start + option.length() );
			int end = value.indexOf( " -" );
			if ( end != -1 )
			{
				value = value.substring( 0, end + 1 );

			}
		}
		//printf("option string %s.\n", value.c_str() );
		return value.trim().trimStart( "=" ).trim();
	}

	/**
	* check whether command line contain an option
	*
	* @param	option - name of the argument
	* @param	argc - total number of argument
	* @param	argv - argument list
	* @return	true if contain the option, otherwise false
	*/

	static bool hasOption ( string option, int argc, char * argv[] )
	{
		string s;
		for ( int i = 0; i < argc; i++ )
		{
			s.append( argv[ i ] );
		}
		return s.toLower().indexOf( option.toLower() ) != -1;
	}


};

#endif
