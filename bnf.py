#!/usr/bin/python
#-*- coding: utf-8 -*-
# This is a demo for parsing a grammar from a BNF-notation.

from pyparse import Parser

p = Parser("$INT /\\d+/ %emit;"
		   "f: INT | '(' e ')';"
		   "mul %emit: t '*' f;"
		   "div %emit: t '/' f;"
		   "t: mul | div | f;"
		   "add %emit: e '+' t;"
		   "sub %emit: e '-' t;"
		   "e %goal: add | sub | t;")


'''
p = Parser("%emitall"
		   "$INT /\\d+/;"
		   "f: INT | '(' e ')';"
		   "t: t '*' f | t '/' f | f;"
		   "e %goal: e '+' t | e '-' t | t;")
'''

p.dump(p.parse("123+456*789"))

