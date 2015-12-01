#!/usr/bin/env python
#-*- coding: utf-8 -*-
# The famous XPL programming language example.
# This little toy C-style language was a demonstraton in the
# UniCC Parser Generator and has been ported to pynetree here.

from pynetree import Parser

p = Parser(
"""
$				/\\s+/													%skip;
$REAL			/\\d+\\.\\d*|\\d*\\.\\d+/								%emit;
$INTEGER		/\\d+/													%emit;
$STRING			/"[^"]*"/												%emit;
$IDENT			/\\w+/													%emit;

program 																%goal
				:	statement* ;

statement		:	"if" '(' expression ')' statement
						('else' statement)?								%emit
				| 	"while" '(' expression ')' statement				%emit
				| 	'{' statement* '}'
				| 	expression ';'
				|	';'
				;

expression		:	expression "==" arith								%emit
        		|	expression "!=" arith								%emit
        		|	expression "<" arith								%emit
        		|	expression ">" arith								%emit
				|	expression "<=" arith								%emit
				|	expression ">=" arith								%emit
				|	assign
				|	arith
				;

assign			:	IDENT "=" expression								%emit
				;

arith			:	arith "+" term										%emit
				|	arith "-" term										%emit
				|	term
				;

term			:	term "*" factor										%emit
				|	term "/" factor										%emit
				|	factor
				;

factor			:	"-" atom											%emit
				|	atom
				;

atom			:	'(' expression ')'
				|	function_call
				|	IDENT
				| 	REAL
				|	INTEGER
				|	STRING
				;

function_call	:	IDENT '(' parameter_list? ')'						%emit
				;

parameter_list	:	parameter_list ',' expression
				|	expression
				;
""")

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
