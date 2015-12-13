#!/usr/bin/env python
#-*- coding: utf-8 -*-
from pynetree import Parser

p = Parser("""
				$/\\s+/ %skip;
				f: [0-9] | '(' e ')';
				mul: t '*' f %emit;
				t: mul | f;
				add: e '+' t %emit;
				e: add | t;""")

p.dump(p.parse("1 + 2 * (3+4) +  5"))
