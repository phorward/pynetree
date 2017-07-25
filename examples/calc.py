#!/usr/bin/env python
#-*- coding: utf-8 -*-
# Demo parser from the README.

from pynetree import Parser

p = Parser({
	"factor": ["@INT", "( expr )"],
	"@mul": "term * factor",
	"@div": "term / factor",
	"term": ["mul", "div", "factor"],
	"@add": "expr + term",
	"@sub": "expr - term",
	"expr": ["add", "sub", "term"],
	"calc$": "expr"
})

p.ignore(r"\s+") #ignore whitespace
p.token("INT", r"\d+")

p.parse("1 + 2 * (3 + 4) + 5").dump()
