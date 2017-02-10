#-*- coding: utf-8 -*-

from pynetree import Parser

p = Parser("""
	%skip /\s+/;
	@int /\d+/;

	factor: int | '(' expr ')';

	@mul: term '*' factor;
	term: mul | factor;

	@add: expr '+' term;
	expr$: add | term;
""")

p.dump(p.parse("1 + 2 * ( 3 + 4 ) * 5"))