##
## Makefile for Address Extractor
##
##

## Set the compiler to be a known ANSI compliant one
CC = g++

## adding the '-DNDEBUG' defines the CT symbol NDEBUG which
## suppresses all the asserts and what not. You'd do that for
## a production build, but it is a good idea to leave it in
## for the purposes of this class.
DFLAG = ## -DNDEBUG

## the -I allows you to include any local header files for our
## class libraries.  
CFLAGS = -g -Wall -Wpointer-arith $(DFLAG)
#LDFLAGS = -g  -lresolv -lprofiler -L/home2/zyu/gprofiler/lib
#LDFLAGS = -g  -lresolv -ltcmalloc -L/home2/zyu/gprofiler/lib
LDFLAGS = -g  -lresolv

HDRS = mystring.h INgrams.h ngrams.h CharNgrams.h WordNgrams.h text2wfreq.h
SRCS = string.cpp INgrams.cpp ngrams.cpp CharNgrams.cpp WordNgrams.cpp text2wfreq.cpp
OBJS = $(SRCS:.c.cpp=.o)
TARGET = ngrams

default : $(TARGET)

ngrams : $(OBJS)
	$(CC) $(OBJS) $(CFLAGS) $(LDFLAGS) -o ngrams


# The dependencies below make use of make's default rules,
# under which a .o automatically depends on its .c and
# the action taken uses the $(CC) and $(CFLAGS) variables.
# These lines describe a few extra dependencies involved.

string.o: mystring.h
INgrams.o: INgrams.h
ngrams.o: ngrams.h
CharNgrams.o: CharNgrams.h
WordNgrams.o: WordNgrams.h
text2wfreq.o: text2wfreq.h

rebuild:
	make clean
	make
clean : 
	@echo "Removing all object files..."
	rm -f core *.o $(TARGET)
