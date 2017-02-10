#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
This is a pynetree grammar definition for a tiny programming language example
called "XPL" (eXample programming language).

XPL defines:

- a typeless language
- arithmetic and conditional expressions
- support of integer, floating point and string values
- simple control structures (conditionals, iterations)
- variable assignments
- nested calls to build-in functions with variable arguments

It can also be perfectly used as an implementation base for any other language.

XPL is implemented in the course of the UniCC Parser Generator's user's manual.

More about XPL can be found here:
http://www.phorward-software.com/software/unicc-lalr1-parser-generator/xpl
"""

from pynetree import Parser

p = Parser(
"""
%skip			/\\s+/ ;

@REAL			/\\d+\\.\\d*|\\d*\\.\\d+/ ;
@INTEGER		/\\d+/ ;
@STRING			/"[^"]*"/ ;
@IDENT			/\\w+/ ;

program$ 		:	statement* ;

statement		:	@("if" '(' expression ')' statement ('else' statement)?)
				| 	@("while" '(' expression ')' statement)
				| 	'{' statement* '}'
				| 	expression ';'
				|	';'
				;

expression		:	@(expression "==" arith)
        		|	@(expression "!=" arith)
        		|	@(expression "<" arith)
        		|	@(expression ">" arith)
				|	@(expression "<=" arith)
				|	@(expression ">=" arith)
				|	assign
				|	arith
				;

@assign			:	IDENT "=" expression ;

arith			:	@(arith "+" term)
				|	@(arith "-" term)
				|	term
				;

term			:	@(term "*" factor)
				|	@(term "/" factor)
				|	factor
				;

factor			:	@("-" atom)
				|	atom
				;

atom			:	'(' expression ')'
				|	function_call
				|	IDENT
				| 	REAL
				|	INTEGER
				|	STRING
				;

@function_call	:	IDENT '(' parameter_list? ')'
				;

parameter_list	:	parameter_list ',' expression
				|	expression
				;
""")

# "99-Bottles-of-Beer" implemented in XPL:

p.dump(p.parse("""
if( ( bottles = prompt( "Enter number of bottles [default=99]" ) ) == "" )
    bottles = 99;

if( integer( bottles ) <= 0 )
{
    print( "Sorry, but the input '" + bottles + "' is invalid." );
    exit( 1 );
}

while( bottles > 0 )
{
    if( bottles > 1 )
        print( bottles + " bottles of beer on the wall, " +
                bottles + " bottles of beer." );
    else
        print( "One bottle of beer on the wall, one bottle of beer." );

    print( "Take one down, pass it around." );

    if( ( bottles = bottles - 1 ) == 0 )
        print( "No more bottles of beer on the wall." );
    else if( bottles == 1 )
        print( "One more bottle of beer on the wall." );
    else
        print( bottles + " more bottles of beer on the wall." );
}
"""))
