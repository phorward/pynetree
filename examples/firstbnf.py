#!/usr/bin/env python
#-*- coding: utf-8 -*-
from pynetree import Parser

p = Parser("""	@int /[0-9]+/;
				%skip /\\s+/ ;

				f: int | '(' e ')';

				@mul: t '*' f;
				t: mul | f;

				@add: e '+' t;
				e: add | t;
			""")

p.dump(p.parse("1 + 2 * (3+4) +  5"))
