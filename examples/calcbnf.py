#!/usr/bin/env python
#-*- coding: utf-8 -*-
# This is a demo for parsing a grammar from a BNF-notation.

from pynetree import Parser

p = Parser("""	%skip /\\s+/;
				@INT /\\d+/;

				f: INT | '(' e ')';
				@mul: t '*' f;
				@div: t '/' f;

				t: mul | div | f;
				@add: e '+' t;
				@sub: e '-' t;

				e$: add | sub | t;
""")

p.parse("123 + 456 * 789").dump()

