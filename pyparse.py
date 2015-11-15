#!/usr/bin/python
#-*- coding: utf-8 -*-
# pyParse v0.1 - A lightweight parsing toolkit written in Python
# Copyright (C) 2015 by Phorward Software Technologies, Jan Max Meyer
# http://www.phorward.info ++ jmm<at>phorward<dot>de
# All rights reserved. See LICENSE for more information.

import re

class SymbolNotFoundError(Exception):
	def __init__(self, name):
		super(SymbolNotFoundError, self).__init__(
			"Symbol not found: '%s'" % name)

class MultipleDefinitionError(Exception):
	def __init__(self, name):
		super(MultipleDefinitionError, self).__init__(
			"Multiple definition of: '%s'" % name)

class Parser(object):
	whitespace = r'\s+'

	grm = {}
	goal = None
	tokens = {}
	actions = {}

	AFTER = 0
	BEFORE = 1
	ITERATE = 2

	def __init__(self, grm, goal = None):
		if isinstance(grm, (str, unicode)):
			self.fromBNF(grm)
		else:
			assert goal, "goal parameter required when " \
						 "grammar is passed via dict"

			if not goal in grm.keys():
				raise SymbolNotFoundError(goal)

			# Check for well-formed production data format,
			# and convert if necessary.
			for n, p in grm.items():
				if not p:
					grm[n] = [""]
				elif not isinstance(p, list):
					grm[n] = [p]

				grm[n] = [x.split() for x in grm[n]]

			# Check for correct goal
			if not goal in grm.keys():
				raise SymbolNotFoundError(goal)

			self.goal = goal
			self.grm = grm

	def fromBNF(self, grm):
		"""
		Compiles a grammar from a BNF-style grammar definition into the
		current Parser object. This function is called internally from
		the constructor of Parser().
		"""
		assert not (self.grm and self.goal), "Grammar must be empty."

		def uniqueName(n):
			while n in self.tokens.keys():
				n += "'"

			while n in self.grm.keys():
				n += "'"

			return n

		def buildSymbol(nonterm, symdef):
			if symdef[0].startswith("mod_"):
				sym = buildSymbol(nonterm, symdef[1][0])

				if "kleene" in symdef[0] or "positive" in symdef[0]:
					oneOrMore = uniqueName(nonterm)
					grm[oneOrMore] = [[oneOrMore, sym], [sym]]
					sym = oneOrMore

				if "optional" in symdef[0] or "kleene" in symdef[0]:
					oneOrNone = uniqueName(nonterm)
					grm[oneOrNone] = [[sym], []]
					sym = oneOrNone

			elif symdef[0] == "inline":
				sym = uniqueName(nonterm)
				grm[sym] = []
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
				if p[0] == "GOAL":
					self.goal = nonterm
					continue
				elif p[0] == "EMIT":
					self.addAction(nonterm)
					continue

				seq = []

				for s in p[1]:
					seq.append(buildSymbol(nonterm, s))

				self.grm[nonterm].append(seq)

		# Construct a parser for the BNF input language.
		bnfparser = Parser({
			"inline": "( alternation )",
			"symbol": ["IDENT", "STRING", "inline", ""],
			"mod_kleene": "symbol *",
			"mod_positive": "symbol +",
			"mod_optional": "symbol ?",
			"modifier": ["mod_kleene", "mod_positive",
						 	"mod_optional", "symbol"],
			"sequence": ["sequence modifier", "modifier"],
			"production": ["sequence", ""],
			"alternation": ["alternation | production", "production"],

			"nontermflag": ["GOAL", "EMIT"],
			"nontermflags": ["nontermflags % nontermflag", "% nontermflag"],
			"opt_nontermflags": ["nontermflags", ""],

			"nontermdef": ["IDENT opt_nontermflags : alternation ;" ],

			"termflag": ["EMIT"],
			"termflags": ["termflags % termflag", "% termflag"],
			"opt_termflags": ["termflags", ""],
			"termsym": ["STRING", "REGEX"],
			"termdef": ["$ IDENT termsym opt_termflags ;"],

			"gflag": ["EMITALL", "EMITNONE"],
			"gflags": ["gflags % gflag", "% gflag"],

			"definition": ["nontermdef", "termdef", "gflags"],
			"definitions": ["definitions definition", "definition"],
			"grammar": "definitions"},

				"grammar")

		bnfparser.addToken("IDENT", r"\w+")
		bnfparser.addToken("STRING", r"'[^']*'")
		bnfparser.addToken("REGEX", r"/(\\.|[^\\/])*/")

		bnfparser.addToken("GOAL", "goal", static=True)
		bnfparser.addToken("EMIT", "emit", static=True)
		bnfparser.addToken("EMITALL", "emitall", static=True)
		bnfparser.addToken("EMITNONE", "emitnone", static=True)

		bnfparser.addAction("IDENT")
		bnfparser.addAction("STRING")
		bnfparser.addAction("REGEX")
		bnfparser.addAction("GOAL")
		bnfparser.addAction("EMIT")
		bnfparser.addAction("EMITALL")
		bnfparser.addAction("EMITNONE")

		bnfparser.addAction("inline")
		bnfparser.addAction("mod_kleene")
		bnfparser.addAction("mod_positive")
		bnfparser.addAction("mod_optional")
		bnfparser.addAction("production")
		bnfparser.addAction("nontermdef")
		bnfparser.addAction("termdef")

		ast = bnfparser.parse(grm)
		if not ast:
			return

		#bnfparser.dump(ast)

		# Integrate all non-terminals into the grammar.
		for d in ast:
			if d[0] == "nontermdef":
				sym = d[1][0][1]
				self.grm[sym] = []

		# Now build the grammar
		emitall = False
		for d in ast:
			if d[0] == "EMITALL":
				emitall = True
				continue
			elif d[0] == "EMITNONE":
				emitall = False
				continue
			elif d[0] == "termdef":
				sym = d[1][0][1]
				dfn = d[1][1][1][1:-1]

				if d[1][1][0] == "REGEX":
					dfn = re.compile(dfn)

				self.tokens[sym] = dfn

				for flag in d[1][2:]:
					if flag[0] == "EMIT":
						self.addAction(sym)

			else:
				sym = d[1][0][1]
				buildNonterminal(sym, d[1][1:])

			if emitall:
				self.addAction(sym)

		# First nonterminal becomes goal, if not set by flags
		if not self.goal:
			for d in ast:
				if d[0] == "nontermdef":
					self.goal = d[1][0][1]
					break

			assert self.goal, "No nonterminal symbol in grammar"

	def addToken(self, name, token, static = False):
		if name in self.tokens.keys() or name in self.grm.keys():
			raise MultipleDefinitionError(name)

		if not static and isinstance(token, (str, unicode)):
			token = re.compile(token)

		self.tokens[name] = token

	def addAction(self, name, func = None, kind = AFTER):
		if not name in self.grm.keys() and not name in self.tokens.keys():
			raise SymbolNotFoundError(name)

		self.actions[name] = (kind, func)

	def reportError(self, s, pos):
		res = re.match(self.whitespace, s[pos:])
		if res:
			pos += len(res.group(0))

		line = s.count("\n", 0, pos) + 1
		col = s.rfind("\n", 0, pos)
		if col < 0:
			col = pos
		else:
			col = pos - col

		print("line %d, col %d: Parse error @ >%s<" % (line, col, s[pos:]))

	def parse(self, s, reduce = True):

		class Entry(object):
			def __init__(self, res = None, pos = 0):
				self.res = res
				self.pos = pos

		class Lr(object):
			def __init__(self, nterm, seed = None, head = None):
				self.nterm = nterm
				self.seed = seed	# The initial parse seed
				self.head = head	# Refers to the head

		class Head(object):
			def __init__(self, nterm):
				self.nterm = nterm
				self.involved = []	# nterminals involved into left-recursion
				self.evaluate = []	# subset of involved non-terminals that may
									# be evaluated

		memo = {}
		lrstack = []
		heads = {}

		def apply(nterm, off):

			def consume(nterm, off):
				"""
				Try to consume any rule of non-terminal ``nterm``
				starting at offset ``off``.
				"""
				for rule in self.grm[nterm]:
					sym = None
					seq = []
					pos = off

					for sym in rule:
						# Skip over whitespace
						if self.whitespace:
							res = re.match(self.whitespace, s[pos:])
							if res:
								pos += len(res.group(0))

						# Is known terminal?
						if sym in self.tokens.keys():
							if isinstance(self.tokens[sym], (str, unicode)):
								if not s[pos:].startswith(self.tokens[sym]):
									break

								seq.append((sym,
									s[pos : pos + len(self.tokens[sym])]))

								pos += len(self.tokens[sym])

							elif callable(self.tokens[sym]):
								res = self.tokens[sym](s, pos)
								if not res:
									break

								seq.append((sym, s[pos : pos + res]))
								pos += res

							else:
								res = re.match(self.tokens[sym], s[pos:])
								if not res:
									break

								seq.append((sym,
									s[pos : pos + len(res.group(0))]))

								pos += len(res.group(0))

						# Is unknown terminal?
						elif not sym in self.grm.keys():
							if not s[pos:].startswith(sym):
								break

							pos += len(sym)

						# Is nonterminal?
						else:
							res = apply(sym, pos)

							if res.res is None:
								break

							pos = res.pos
							if res.res:
								seq.append((sym, res.res))

						sym = None

					if not sym:
						return (seq, pos)

				return (None, off)

			def lrgrow(entry, head):
				#print("lrgrow", nterm)
				heads[off] = head

				while True:
					pos = off
					head.evaluate = list(head.involved)

					res, pos = consume(nterm, pos)
					if not res or pos <= entry.pos:
						break

					entry.res = res
					entry.pos = pos

				del heads[off]
				return entry

			def lrstart(entry):
				#print("lrstart", nterm)
				lr = entry.res

				if not lr.head:
					lr.head = Head(nterm)

				for item in reversed(lrstack):
					if item.head == lr.head:
						break

					item.head = lr.head
					lr.head.involved.append(item.nterm)

			def lranswer(entry):
				#print("lranswer", nterm)

				head = entry.res.head
				if head.nterm != nterm:
					return Entry(entry.res.seed, entry.pos)

				entry.res = entry.res.seed
				if not entry.res:
					return Entry(None, entry.pos)

				return lrgrow(entry, head)

			def recall():
				entry = memo.get((nterm, off))
				head = heads.get(off)

				if not head:
					return entry

				if (not entry
					and nterm not in [head.nterm] + head.involved):
					return Entry(None, off)

				if nterm in head.evaluate:
					head.evaluate.remove(nterm)
					entry.res, entry.pos = consume(nterm, off)

				return entry

			entry = recall()

			if entry is None:
				lr = Lr(nterm)
				lrstack.append(lr)

				# mark this a fail to avoid left-recursions
				memo[(nterm, off)] = entry = Entry(lr, off)

				res, pos = consume(nterm, off)

				lrstack.pop()

				entry.pos = pos
				if lr.head:
					lr.seed = res
					return lranswer(entry)

				entry.res = res

			elif entry.res and isinstance(entry.res, Lr):
				lrstart(entry)
				return Entry(entry.res.seed, entry.pos)

			return entry

		ast = apply(self.goal, 0)
		if not ast or ast.pos < len(s):
			# On parse error, try to find longest match from memo cache
			last = ast.pos if ast else 0

			for (nterm, off) in memo.keys():
				if off > last:
					last = off

			if last > 0:
				self.reportError(s, last)

			return None

		res = (self.goal, ast.res)
		return self.reduce(res) if reduce else res

	def reduce(self, ast):
		if ast is None:
			return None

		if isinstance(ast, tuple):
			if isinstance(ast[1], list):
				if ast[0] in self.actions.keys():
					return (ast[0], self.reduce(ast[1]))

				return self.reduce(ast[1])

			elif ast[0] in self.actions.keys():
				return ast
		else:
			ret = []

			for i in ast:
				res = self.reduce(i)

				if res:
					if isinstance(res, list):
						ret.extend(res)
					else:
						ret.append(res)

			#if len(ret) == 1:
			#	ret = ret[0]

			if ret:
				return ret

		return None

	def __callAction(self, item, kind):
		if (item[0] in self.actions.keys()
			and self.actions[item[0]][0] == kind):
			action = self.actions[item[0]][1]

			if callable(action):
				action(item)
			elif not action is None:
				print(action)
			else:
				print(item[1])

	def traverse(self, ast):
		if isinstance(ast, tuple):
			self.__callAction(ast, self.BEFORE)

			if isinstance(ast[1], list) or isinstance(ast[1], tuple):
				self.traverse(ast[1])

			self.__callAction(ast, self.AFTER)
		else:
			for i in ast:
				self.traverse(i)
				self.__callAction(ast, self.ITERATE)

	def dump(self, ast, level = 0):
		if ast is None:
			return

		if isinstance(ast, tuple):
			if isinstance(ast[1], (list, tuple)) or not ast[1]:
				print("%s%s" % (level * " ", ast[0]))
				self.dump(ast[1], level + 1)
			else:
				print("%s%s (%s)" % (level * " ", ast[0], ast[1]))
		else:
			for i in ast:
				self.dump(i, level + 1 if level > 0 else level)


if __name__ == "__main__":

	class Interpreter(Parser):
		stack = []

		def push(self, elem):
			self.stack.append(float(elem[1]))


		def add(self, elem):
			self.stack.append(self.stack.pop() + self.stack.pop())

		def sub(self, elem):
			x = self.stack.pop()
			self.stack.append(self.stack.pop() - x)

		def mul(self, elem):
			self.stack.append(self.stack.pop() * self.stack.pop())

		def div(self, elem):
			x = self.stack.pop()
			self.stack.append(self.stack.pop() / x)

		def result(self, elem):
			print(self.stack.pop())

		# def apush(self, elem):
		# 	print("PUSH %s" % elem[1])
		#
		# def aadd(self, elem):
		# 	print("ADD")
		#
		# def asub(self, elem):
		# 	print("SUB")
		#
		# def amul(self, elem):
		# 	print("MUL")
		#
		# def adiv(self, elem):
		# 	print("DIV")
		#
		# def aresult(self, elem):
		# 	print("PRINT")

	# RIGHT-RECURSIVE
	'''
	g = {
		"factor": ["INT", "( expr )"],
		"term": ["factor * term", "factor / term", "factor"],
		"expr": ["term + expr", "term - expr", "term"],
		"calc": "expr"
	}
	'''

	# DIRECT LEFT-RECURSIVE
	'''
	g = {
		"factor": ["INT", "( expr )"],
		"term": ["term * factor", "factor"],
		"expr": ["expr + term", "expr - term", "term"],
		"calc": "expr"
	}
	'''

	# INDIRECT LEFT-RECURSIVE!!
	g = {
		"factor": ["INT", "( expr )"],
		"mul": "term * factor",
		"div": "term / factor",
		"term": ["mul", "div", "factor"],
		"add": "expr + term",
		"sub": "expr - term",
		"expr": ["add", "sub", "term"],
		"calc": "expr"
	}

	i = Interpreter(g, "calc")
	i.addToken("INT", r"\d+")

	i.addAction("INT", i.push)
	i.addAction("mul", i.mul)
	i.addAction("div", i.div)
	i.addAction("add", i.add)
	i.addAction("sub", i.sub)
	i.addAction("calc", i.result)

	# Parse into a parse tree
	ptree = i.parse("1 + 2 * ( 3 + 4 ) * 5 - 6 / 7", reduce=False)

	print("--- parse tree ---")
	i.dump(ptree)

	# Turn into an abstract syntax tree (ast)
	ast = i.reduce(ptree)

	print("--- abstract syntax tree ---")
	i.dump(ast)

	# Interpret the ast (works also with the syntax tree!)
	print("--- traversal ---")
	i.traverse(ast)

	# # Compile into assembly?
	# i.addAction("INT", i.apush)
	# i.addAction("mul", i.amul)
	# i.addAction("div", i.adiv)
	# i.addAction("add", i.aadd)
	# i.addAction("sub", i.asub)
	# i.addAction("calc", i.aresult)
	#
	# print("--- assembly traversal ---")
	# i.traverse(ast)
