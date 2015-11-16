#-*- coding: utf-8 -*-
# Demo parser from the README.

from pyparse import Parser

p = Parser({
	"factor": ["INT", "( expr )"],
	"mul": "term * factor",
	"div": "term / factor",
	"term": ["mul", "div", "factor"],
	"add": "expr + term",
	"sub": "expr - term",
	"expr": ["add", "sub", "term"],
	"calc$": "expr"
})

p.addToken("INT", r"\d+")

p.addAction("INT")
p.addAction("mul")
p.addAction("div")
p.addAction("add")
p.addAction("sub")
p.addAction("calc")

p.dump(p.parse("1 + 2 * (3 + 4) + 5"))
