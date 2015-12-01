#!/usr/bin/env python
#-*- coding: utf-8 -*-
from pynetree import Parser

p = Parser({
	"factor": ["INT", "( expr )"],
	"mul": "term * factor",
	"term": ["mul", "factor"],
	"add": "expr + term",
	"expr": ["add", "term"],
	"calc$": "expr"
})

p.ignore(r"\s+")
p.token("INT", r"\d+")
p.emit(["INT", "mul", "add"])

p.dump(p.parse("1 + 2 * (3 + 4) + 5"))