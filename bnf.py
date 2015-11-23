#!/usr/bin/python
#-*- coding: utf-8 -*-
# This is a demo for parsing a grammar from a BNF-notation.

from pynetree import Parser

p = Parser("""	$INT /\\d+/ %emit;
				f: INT | '(' e ')';
				mul: t "*" f %emit;
				div: t "/" f %emit;
				t: mul | div | f;
				add: e "+" t %emit;
				sub: e "-" t %emit;
				e %goal: add | sub | t;""")

p.dump(p.parse("123+456*789"))

