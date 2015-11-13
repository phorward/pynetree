#!/usr/bin/python
#-*- coding: utf-8 -*-
# pyParse v0.1 - A lightweight parsing toolkit written in Python
# Copyright (C) 2015 by Phorward Software Technologies, Jan Max Meyer
# http://www.phorward.info ++ jmm<at>phorward<dot>de
# All rights reserved. See LICENSE for more information.

from pyparse import Parser

class Grammar(Parser):


	def __init__(self, grm):
		self.parser = Parser({	"inline": "( alternation )",
								"symbol": ["IDENT", "STRING", ""],
								"mod_kleene": "symbol *",
								"mod_positive": "symbol +",
								"mod_optional": "symbol ?",
								"modifier": ["mod_kleene", "mod_positive", "mod_optional", "symbol"],
								"sequence": ["sequence modifier", "modifier"],
								"production": ["sequence", ""],
								"alternation": ["alternation | production", "production"],
								"nontermdef": [ "IDENT : alternation ;" ],
								"definition": ["nontermdef"],
								"definitions": ["definitions definition", "definition"],
								"grammar": "definitions"},
							 "grammar")

		self.parser.addToken("IDENT", r"\w+")
		self.parser.addToken("STRING", r"'[^']*'")

		self.parser.addAction("inline", "INLINE")
		self.parser.addAction("symbol", "SYM")
		self.parser.addAction("mod_kleene", "KLE")
		self.parser.addAction("mod_positive" "POS")
		self.parser.addAction("mod_optional", "OPT")
		self.parser.addAction("production", "PROD")
		self.parser.addAction("nontermdef", "NONTERM")
		self.parser.addAction("IDENT")
		self.parser.addAction("STRING")

		self.parser.dump(self.parser.parse(grm))

Grammar("f: INT | '(' e ')'; t: t '*' f | t '/' f | f; e: e '+' t | e '-' t | t;")
