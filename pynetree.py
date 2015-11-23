#!/usr/bin/python
#-*- coding: utf-8 -*-
# >>>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# pynetree v0.1 - A light-weight parsing toolkit written in Python
# Copyright (C) 2015 by Phorward Software Technologies, Jan Max Meyer
# www.phorward.info ++ jmm<at>phorward<dot>de
# All rights reserved. See LICENSE for more information.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~<<<

import re

class GoalSymbolNotDefined(Exception):
	def __init__(self):
		super(GoalSymbolNotDefined, self).__init__(
			"No goal symbol defined in provided grammar")

class SymbolNotFoundError(Exception):
	def __init__(self, name):
		super(SymbolNotFoundError, self).__init__(
			"Symbol not found: '%s'" % name)

class MultipleDefinitionError(Exception):
	def __init__(self, name):
		super(MultipleDefinitionError, self).__init__(
			"Multiple definition of: '%s'" % name)

class Parser(object):
	AFTER = 0
	BEFORE = 1
	ITERATE = 2

	def __init__(self, grm):
		"""
		Constructs a new parser object.

		:param grm: The grammar to be used; This can either be a dictionary of
					symbols and relating productions, or a string that is
					expressed in the BNF-styled grammar definition parser.
		:type grm: dict | str
		:param goal: This must be provided when ``grm`` contains a dict.
		:type goal: str
		"""
		self.whitespace = r'\s+'

		self.grammar = {}
		self.goal = None
		self.tokens = {}
		self.emits = {}

		def uniqueName(n):
			"""
			Generates a unique symbol name from ``n``, by adding
			single-quotation characters to the end of ``n`` until
			there is no symbol with such name.

			:param n: The basename to become unique.
			:type n: str

			:return: The next unique symbol name.
			:rtype: str
			"""
			while n in self.tokens.keys():
				n += "'"

			while n in self.grammar.keys():
				n += "'"

			return n

		def generateModifier(nonterm, sym, mod):
			if mod in ["*", "+"]:
				oneOrMore = uniqueName(nonterm)
				self.grammar[oneOrMore] = [[oneOrMore, sym], [sym]]
				sym = oneOrMore

			if mod in ["?", "*"]:
				oneOrNone = uniqueName(nonterm)
				self.grammar[oneOrNone] = [[sym], []]
				sym = oneOrNone

			return sym


		if isinstance(grm, dict):
			# Rewrite grammar modifiers and goal according to the provided
			# grammar
			for n, np in grm.items():
				if n.endswith("$"):
					n = n[:-1]
					self.goal = n

				if not np:
					self.grammar[n] = [""]
				elif not isinstance(np, list):
					self.grammar[n] = [np]
				else:
					self.grammar[n] = np[:]

				np = self.grammar[n] = [x.split() for x in self.grammar[n]]

				rnp = []
				for p in np:

					rp = []
					for sym in p:
						if any([len(sym) > 1 and sym.endswith(x)
									for x in "*+?"]):
							sym = generateModifier(n, sym[:-1], sym[-1:])

						rp.append(sym)

					rnp.append(rp)

				self.grammar[n] = rnp
		else:
			# Construct a parser for the BNF input language.
			bnfparser = Parser({
				"inline": "( alternation )",
				"symbol": ["IDENT", "STRING", "TOKEN", "inline", ""],
				"mod_kleene": "symbol *",
				"mod_positive": "symbol +",
				"mod_optional": "symbol ?",
				"modifier": ["mod_kleene", "mod_positive",
								"mod_optional", "symbol"],
				"sequence": ["sequence modifier", "modifier"],

				"prodflag": ["EMIT", "NOEMIT"],
				"prodflags": ["prodflags % prodflag+", "% prodflag+"],

				"production": ["sequence? prodflags?"],

				"alternation": ["alternation | production", "production"],

				"nontermflag": ["GOAL", "EMIT", "NOEMIT"],
				"nontermflags": ["nontermflags % nontermflag", "% nontermflag"],

				"nontermdef": ["IDENT nontermflags? : alternation ;" ],

				"termflag": ["EMIT"],
				"termflags": ["termflags % termflag", "% termflag"],
				"termsym": ["STRING", "REGEX"],
				"termdef": ["$ IDENT termsym termflags? ;"],

				"gflag": ["EMITALL", "EMITNONE"],
				"gflags": ["gflags % gflag", "% gflag"],

				"definition": ["nontermdef", "termdef", "gflags"],
				"definitions": ["definitions definition", "definition"],
				"grammar$": "definitions"})

			bnfparser.token("IDENT", r"\w+")
			bnfparser.token("STRING", r"'[^']*'")
			bnfparser.token("TOKEN", r'"[^"]*"')
			bnfparser.token("REGEX", r"/(\\.|[^\\/])*/")

			bnfparser.token("GOAL", "goal", static=True)
			bnfparser.token("EMIT", "emit", static=True)
			bnfparser.token("NOEMIT", "noemit", static=True)
			bnfparser.token("EMITALL", "emitall", static=True)
			bnfparser.token("EMITNONE", "emitnone", static=True)

			bnfparser.emit(["IDENT", "STRING", "TOKEN", "REGEX", "GOAL", "EMIT", "NOEMIT", "EMITALL", "EMITNONE"])
			bnfparser.emit(["inline", "mod_kleene", "mod_positive", "mod_optional",
							"production",  "nontermdef", "termdef"])

			ast = bnfparser.parse(grm)
			if not ast:
				raise SyntaxError()

			def buildSymbol(nonterm, symdef):
				if symdef[0].startswith("mod_"):
					sym = buildSymbol(nonterm, symdef[1][0])
					sym = generateModifier(nonterm, sym,
										   {"kleene":"*",
											"positive":"+",
											"optional":"?"}[symdef[0][4:]])
				elif symdef[0] == "inline":
					sym = uniqueName(nonterm)
					self.grammar[sym] = []
					buildNonterminal(sym, symdef[1])
				elif symdef[0] == "TOKEN":
					sym = symdef[1][1:-1]
					self.tokens[sym] = sym
					self.emits[sym] = (self.AFTER, None)
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
						self.emit(nonterm)
						continue

					seq = []

					for s in p[1]:
						if s[0] == "EMIT":
							self.emits["%s[%d]" % (nonterm, len(self.grammar[nonterm]))] = (None, self.AFTER)
							continue

						seq.append(buildSymbol(nonterm, s))

					self.grammar[nonterm].append(seq)

			#bnfparser.dump(ast)

			# Integrate all non-terminals into the grammar.
			for d in ast:
				if d[0] == "nontermdef":
					sym = d[1][0][1]
					self.grammar[sym] = []

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
							self.emit(sym)

				else:
					sym = d[1][0][1]
					buildNonterminal(sym, d[1][1:])

				if emitall:
					self.emit(sym)

			# First nonterminal becomes goal, if not set by flags
			if not self.goal:
				for d in ast:
					if d[0] == "nontermdef":
						self.goal = d[1][0][1]
						break

		if not self.goal:
			raise GoalSymbolNotDefined()


	def token(self, name, token = None, static = False):
		if isinstance(name, list):
			for n in name:
				self.token(n, token=token, static=static)

			return


		if name in self.tokens.keys() or name in self.grammar.keys():
			raise MultipleDefinitionError(name)

		if token:
			if not static and isinstance(token, (str, unicode)):
				token = re.compile(token)
		else:
			token = str(name)

		self.tokens[name] = token

	def emit(self, name, action = None, kind = AFTER):
		if isinstance(name, list):
			for n in name:
				self.emit(n, action=action, kind=kind)

			return

		if not name in self.grammar.keys() and not name in self.tokens.keys():
			res = re.match(r"(\w+)\[\d+\]", ast[0])
			if not res or not res.group(1) in self.grammar.keys():
				raise SymbolNotFoundError(name)

		self.emits[name] = (kind, action)

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

			def skipwhitespace(s, pos):
				# Skip over whitespace
				if self.whitespace:
					res = re.match(self.whitespace, s[pos:])
					if res:
						return pos + len(res.group(0))

				return pos

			def consume(nterm, off):
				"""
				Try to consume any rule of non-terminal ``nterm``
				starting at offset ``off``.
				"""
				count = 0
				for rule in self.grammar[nterm]:
					sym = None
					seq = []
					pos = off

					for sym in rule:
						pos = skipwhitespace(s, pos)

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
						elif not sym in self.grammar.keys():
							if not s[pos:].startswith(sym):
								break

							#seq.append((sym, s[pos : pos + len(sym)]))
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
						pos = skipwhitespace(s, pos)

						# Insert production-based node?
						if ("%s[%d]" % (nterm, count)) in self.emits:
							seq = [("%s[%d]" % (nterm, count), seq)]

						return (seq, pos)

					count += 1

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
				if ast[0] in self.emits.keys():

					# Remove production node format, if available
					res = re.match(r"(\w+)\[\d+\]", ast[0])
					if res:
						return (res.group(1), self.reduce(ast[1]))

					return (ast[0], self.reduce(ast[1]))

				return self.reduce(ast[1])

			elif ast[0] in self.emits.keys():
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
		if (item[0] in self.emits.keys()
			and self.emits[item[0]][0] == kind):
			action = self.emits[item[0]][1]

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

	class Calculator(Parser):
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

	# RIGHT-RECURSIVE
	'''
	g = {
		"factor": ["INT", "( expr )"],
		"term": ["factor * term", "factor / term", "factor"],
		"expr": ["term + expr", "term - expr", "term"],
		"calc$": "expr"
	}
	'''

	# DIRECT LEFT-RECURSIVE
	'''
	g = {
		"factor": ["INT", "( expr )"],
		"term": ["term * factor", "factor"],
		"expr": ["expr + term", "expr - term", "term"],
		"calc$": "expr"
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
		"calc$": "expr"
	}

	calc = Calculator(g)
	calc.token("INT", r"\d+")

	calc.emit("INT", calc.push)
	calc.emit("mul", calc.mul)
	calc.emit("div", calc.div)
	calc.emit("add", calc.add)
	calc.emit("sub", calc.sub)
	calc.emit("calc", calc.result)

	# Parse into a parse tree
	ptree = calc.parse("1 + 2 * ( 3 + 4 ) * 5 - 6 / 7", reduce=False)

	print("--- entire parse tree ---")
	calc.dump(ptree)

	# Turn into an abstract syntax tree (ast)
	ast = calc.reduce(ptree)

	print("--- abstract syntax tree ---")
	calc.dump(ast)

	# Interpret the AST (works also with the entire parse tree!)
	print("--- traversal ---")
	calc.traverse(ast)
