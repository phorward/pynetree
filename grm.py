#!/usr/bin/python
#-*- coding: utf-8 -*-
# pyParse v0.1 - A lightweight parsing toolkit written in Python
# Copyright (C) 2015 by Phorward Software Technologies, Jan Max Meyer
# http://www.phorward.info ++ jmm<at>phorward<dot>de
# All rights reserved. See LICENSE for more information.

from pyparse import Parser
import re

class Grammar(Parser):
	parser = None

	def __init__(self, grm):
		grammar = {}
		tokens = {}

		def uniqueName(n):
			while n in tokens.keys():
				n += "'"

			while n in grammar.keys():
				n += "'"

			return n

		def buildSymbol(nonterm, symdef):
			if symdef[0].startswith("mod_"):
				sym = buildSymbol(nonterm, symdef[1][0])

				if "kleene" in symdef[0] or "positive" in symdef[0]:
					oneOrMore = uniqueName(nonterm)
					grammar[oneOrMore] = [[oneOrMore, sym], [sym]]
					sym = oneOrMore

				if "optional" in symdef[0] or "kleene" in symdef[0]:
					oneOrNone = uniqueName(nonterm)
					grammar[oneOrNone] = [[sym], []]
					sym = oneOrNone

			elif symdef[0] == "inline":
				sym = uniqueName(nonterm)
				grammar[sym] = []
				buildNonterminal(sym, symdef[1])

			elif symdef[0] != "IDENT":
				sym = symdef[1][1:-1]
			else:
				sym = symdef[1]

			return sym

		def buildNonterminal(nonterm, prods):
			if isinstance(prods, tuple):
				prods = [prods]

			for p in prods:
				seq = []

				for s in p[1]:
					seq.append(buildSymbol(nonterm, s))

				grammar[nonterm].append(seq)


		self.parser = Parser({	"inline": "( alternation )",
								"symbol": ["IDENT", "STRING", "inline", ""],
								"mod_kleene": "symbol *",
								"mod_positive": "symbol +",
								"mod_optional": "symbol ?",
								"modifier": ["mod_kleene", "mod_positive", "mod_optional", "symbol"],
								"sequence": ["sequence modifier", "modifier"],
								"production": ["sequence", ""],
								"alternation": ["alternation | production", "production"],
								"nontermdef": ["IDENT : alternation ;" ],
								"termsym": ["STRING", "REGEX"],
								"termdef": ["$ IDENT termsym ;"],
								"definition": ["nontermdef", "termdef"],
								"definitions": ["definitions definition", "definition"],
								"grammar": "definitions"},
							 "grammar")

		self.parser.addToken("IDENT", r"\w+")
		self.parser.addToken("STRING", r"'[^']*'")
		self.parser.addToken("REGEX", r"/(\\.|[^\\/])*/")

		self.parser.addAction("IDENT")
		self.parser.addAction("STRING")
		self.parser.addAction("REGEX")
		self.parser.addAction("inline")
		self.parser.addAction("mod_kleene")
		self.parser.addAction("mod_positive")
		self.parser.addAction("mod_optional")
		self.parser.addAction("production")
		self.parser.addAction("nontermdef")
		self.parser.addAction("termdef")

		ast = self.parser.parse(grm)
		if not ast:
			return

		self.parser.dump(ast)

		# Integrate all non-terminals into the grammar.
		for d in ast:
			if d[0] == "nontermdef":
				sym = d[1][0][1]
				grammar[sym] = []
			elif d[0] == "termdef":
				sym = d[1][0][1]
				dfn = d[1][1][1][1:-1]

				if d[1][1][0] == "REGEX":
					dfn = re.compile(dfn)

				tokens[sym] = dfn

		# Now build the grammar
		for d in ast:
			if not d[0] == "nontermdef":
				continue

			buildNonterminal(d[1][0][1], d[1][1:])

		print(grammar)

Grammar("$INT /\d+/; f: INT | '(' e ')'; t: t '*' f | t '/' f | f; e: e '+' t | e '-' t | t;")
#Grammar("f: INT+; g: ROFL COPTER (x |y)*;")
