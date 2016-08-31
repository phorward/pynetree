#!/usr/bin/env python
#-*- coding: utf-8 -*-
# >>>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# pynetree - A light-weight parsing toolkit written in Python
# Copyright (C) 2015, 2016 by Phorward Software Technologies, Jan Max Meyer
# www.phorward.info ++ jmm<at>phorward<dot>de
# All rights reserved. See LICENSE for more information.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~<<<

"""
pynetree is a simple, light-weight parsing toolkit for and written in Python.
"""

__author__ = "Jan Max Meyer"
__copyright__ = "Copyright 2015-2016, Phorward Software Technologies"
__version__ = "0.3"
__license__ = "MIT"
__status__ = "Production"

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

class Node(object):
	"""
	This is an AST node.
	"""

	def __init__(self, symbol, match = None, rule = None, children = None):
		self.symbol = symbol
		self.rule = rule
		self.match = match
		self.children = children or []

	def __str__(self):
		s = self.symbol

		if self.rule:
			s += "[%d]" % self.rule

		if self.match:
			s += " (%s)" % self.match

		return s

class Parser(object):
	"""
	The main parser class that implements a pynetree parser.

	The class provides functions for defining the grammar,
	parsing input, dumping and traversing the resulting parse
	tree or abstract syntax tree.
	"""
	AUTOTOKNAME = "$%03d"

	def __init__(self, grm):
		"""
		Constructs a new pynetree Parser object.

		:param grm: The grammar to be used; This can either be a dictionary of
					symbols and relating productions, or a string that is
					expressed in the BNF-styled grammar definition parser.
		:type grm: dict | str
		"""
		self.grammar = {}
		self.goal = None
		self.tokens = {}
		self.ignores = []
		self.emits = {}

		def uniqueName(n):
			"""
			Generates a unique symbol name from ``n``, by adding
			single-quotation characters to the end of ``n`` until
			no symbol with such a name exists in the grammar.
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
				"symbol": ["IDENT", "STRING", "TOKEN", "REGEX", "CCL",
						   	"inline", ""],
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

				"termflag": ["EMIT", "IGNORE"],
				"termflags": ["termflags % termflag", "% termflag"],
				"termsym": ["STRING", "REGEX", "CCL", "IDENT"],
				"opt_ident": ["IDENT", ""],
				"termdef": ["$ opt_ident termsym termflags? ;"],

				"gflag": ["EMITALL", "EMITNONE"],
				"gflags": ["gflags % gflag", "% gflag"],

				"definition": ["nontermdef", "termdef", "gflags"],
				"definitions": ["definitions definition", "definition"],
				"grammar$": "definitions"})

			bnfparser.ignore(r"\s+")
			bnfparser.token("IDENT", r"\w+")
			bnfparser.token("CCL", r"\[[^\]]*\]")
			bnfparser.token("STRING", r"'[^']*'")
			bnfparser.token("TOKEN", r'"[^"]*"')
			bnfparser.token("REGEX", r"/(\\.|[^\\/])*/")

			bnfparser.token("GOAL", "goal", static=True)
			bnfparser.token("EMIT", "emit", static=True)
			bnfparser.token("NOEMIT", "noemit", static=True)
			bnfparser.token("EMITALL", "emitall", static=True)
			bnfparser.token("EMITNONE", "emitnone", static=True)
			bnfparser.token("IGNORE", r"ignore|skip")

			bnfparser.emit(["IDENT", "STRING", "TOKEN", "REGEX", "CCL",
							"GOAL", "EMIT", "NOEMIT", "EMITALL", "EMITNONE",
							"IGNORE"])
			bnfparser.emit(["inline", "mod_kleene", "mod_positive",
							"mod_optional", "production",  "nontermdef",
							"termdef", "opt_ident"])

			ast = bnfparser.parse(grm)
			if not ast:
				raise SyntaxError()

			def buildSymbol(nonterm, symdef):
				"""
				AST traversal function for symbol level in the BNF-grammar.
				"""

				if symdef.symbol.startswith("mod_"):
					sym = buildSymbol(nonterm, symdef.children[0])
					sym = generateModifier(nonterm, sym,
										   {"kleene":"*",
											"positive":"+",
											"optional":"?"}[symdef.symbol[4:]])
				elif symdef.symbol == "inline":
					sym = uniqueName(nonterm)
					self.grammar[sym] = []
					buildNonterminal(sym, symdef.children)
				elif symdef.symbol == "TOKEN":
					sym = symdef.match[1:-1]
					self.tokens[sym] = sym
					self.emits[sym] = None
				elif symdef.symbol == "REGEX":
					sym = uniqueName(nonterm.upper())
					self.token(sym, symdef.match[1:-1])
					self.emits[sym] = None
				elif symdef.symbol == "CCL":
					sym = uniqueName(nonterm.upper())
					self.token(sym, symdef.match)
				elif symdef.symbol == "STRING":
					sym = symdef.match[1:-1]
				else:
					sym = symdef.match

				return sym

			def buildNonterminal(nonterm, prods, allEmit = False):
				"""
				AST traversal function for nonterminals in the BNF-grammar.
				"""
				if isinstance(prods, tuple):
					prods = [prods]

				emits = []

				for p in prods:

					if p.symbol == "GOAL":
						self.goal = nonterm
						continue

					elif p.symbol == "EMIT":
						allEmit = True
						continue

					elif p.symbol == "NOEMIT":
						allEmit = False
						continue

					seq = []
					emit = allEmit

					for s in p.children:

						if s.symbol == "EMIT":
							emit = True
							continue

						elif s.symbol == "NOEMIT":
							emit = False
							continue

						seq.append(buildSymbol(nonterm, s))

					if emit:
						emits.append((nonterm, len(self.grammar[nonterm])))

					self.grammar[nonterm].append(seq)

				if len(self.grammar[nonterm]) == len(emits):
					self.emit(nonterm)
				else:
					for i in emits:
						self.emit(i)

			#bnfparser.dump(ast)

			# Integrate all non-terminals into the grammar.
			for d in ast:
				if d.symbol == "nontermdef":
					sym = d.children[0].match
					self.grammar[sym] = []

			# Now build the grammar
			emitall = False
			for d in ast:
				if d.symbol == "EMITALL":
					emitall = True
					continue
				elif d.symbol == "EMITNONE":
					emitall = False
					continue
				elif d.symbol == "termdef":
					if d.children[0].children:
						sym = d.children[0].children[0].match
					else:
						sym = self.AUTOTOKNAME % (len(self.tokens.keys()) + 1)

					kind = d.children[1].symbol

					if kind == "STRING":
						dfn = d.children[1].children[0].match[1:-1]
					elif kind == "REGEX":
						dfn = re.compile(d.children[1].match[1:-1])
					elif kind == "CCL":
						dfn = re.compile(d.children[1].match)
					else:
						dfn = d.children[1].match

					if sym in self.tokens.keys():
						raise MultipleDefinitionError(sym)

					self.tokens[sym] = dfn

					for flag in d.children[2:]:
						if flag.symbol == "EMIT":
							self.emit(sym)
						elif flag.symbol == "IGNORE":
							self.ignores.append(sym)

					if emitall:
						self.emit(sym)

				else:
					sym = d.children[0].match
					buildNonterminal(sym, d.children[1:], emitall)

			# First nonterminal becomes goal, if not set by flags
			if not self.goal:
				for d in reversed(ast):
					if d.symbol == "nontermdef":
						self.goal = d.children[0].match
						break

		if not self.goal:
			raise GoalSymbolNotDefined()


	def token(self, name, token = None, static = False):
		"""
		Adds a new terminal token ``name`` to the parser.

		:param name: The unique, identifying name of the token to be added.
		:type name: str

		:param token: The token definition that is registered with ``name``.
			If this is a str, and ``static`` is False, it will be interpreted
			as regular expression. If omitted, ``token`` is set to ``name`` as
			static string.
		:type token: str | re | callable

		:param static: If True, ``token`` is direcly taken as is, and not
			interpreted as a regex str.
		"""

		if isinstance(name, list):
			for n in name:
				self.token(n, token=token, static=static)

			return

		if name in self.tokens.keys() or name in self.grammar.keys():
			raise MultipleDefinitionError(name)

		if token:
			if not static and isinstance(token, str):
				token = re.compile(token)
		else:
			token = str(name)

		self.tokens[name] = token

	def ignore(self, token, static = False):
		"""
		Adds a new ignore terminal (whitespace) to the parser.

		:param token: The token definition of the whitespace symbol.
			If this is a str, and ``static`` is False, it will be interpreted
			as regular expression.
		:type token: str | re | callable

		:param static: If True, ``token`` is direcly taken as is, and not
			interpreted as a regex str.
		"""

		name = self.AUTOTOKNAME % len(self.tokens.keys())
		self.token(name, token, static)
		self.ignores.append(name)

	def emit(self, name, action = None):
		"""
		Defines which symbols of the grammar shall be emitted in the
		generated, abstract syntax tree (AST).

		:param name: The name of the symbol that shall be emitted.
			Alternatively, a list of symbol names is accepted.
		:type name: str | list

		:param action: An action that can be associated with the
			emitter during AST traversal. This can be omitted, if
			the traversal function is manually written.
		:type action: callable
		"""

		if isinstance(name, list):
			for n in name:
				self.emit(n, action)

			return

		if isinstance(name, tuple):
			testname = name[0]
		else:
			testname = name

		if (not testname in self.grammar.keys()
			and not testname in self.tokens.keys()):
			raise SymbolNotFoundError(testname)

		self.emits[name] = action

	def error(self, s, pos):
		"""
		Print a parse error, that oocurs on input ``s`` at offset ``pos``.
		This function can be overridden for specific operations.

		:param s: The entire input string.
		:type s: str

		:param pos: The offset where the syntax error occurs.
		:param pos: int | long
		"""
		line = s.count("\n", 0, pos) + 1

		col = s.rfind("\n", 0, pos)
		col = pos if col < 0 else pos - col

		print("line %d, col %d: Parse error @ >%s<" % (line, col, s[pos:]))

	def parse(self, s):
		"""
		Parse ``s`` with the currently defined grammar.

		This invokes the parser on a given input, and returns the
		abstract syntax tree of this input on success.

		The parser is implemented as a modified packrat parsing algorithm,
		with support of left-recursive grammars.

		:param s: The input string to be parsed.
		:param s: str

		:returns: Abstract syntax tree, None on error.
		:rtype: list | tuple
		"""

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
			"""
			Apply nonterminal ``nterm`` on offset ``off``.
			"""

			def scantoken(sym, s, pos):
				"""
				Scan for a token that was previously defined with token().
				"""
				if isinstance(self.tokens[sym], str):
					if s.startswith(self.tokens[sym], pos):
						return len(self.tokens[sym])

				elif callable(self.tokens[sym]):
					res = self.tokens[sym](s, pos)
					if res:
						return res

				else:
					res = self.tokens[sym].match(s[pos:])
					if res and s.startswith(res.group(0), pos):
						return len(res.group(0))

				return -1

			def scanwhitespace(s, pos):
				"""
				Scan for whitespace that was previously defined by ignore().
				"""
				while True:
					i = 0
					for sym in self.ignores:
						res = scantoken(sym, s, pos)
						if res > 0:
							pos += res
							break

						i += 1

					if i == len(self.ignores):
						break

				return pos

			def consume(nterm, off):
				"""
				Try to consume any rule of non-terminal ``nterm``
				starting at offset ``off``.
				"""
				#print("consume", nterm, off)
				count = 0
				for rule in self.grammar[nterm]:
					sym = None
					seq = []
					pos = off

					for sym in rule:
						pos = scanwhitespace(s, pos)

						# Is known terminal?
						if sym in self.tokens.keys():
							res = scantoken(sym, s, pos)
							if res <= 0:
								break

							if sym in self.emits.keys():
								seq.append(Node(sym, s[pos:pos + res]))

							pos += res

						# Is unknown terminal?
						elif not sym in self.grammar.keys():
							if not s[pos:].startswith(sym):
								break

							pos += len(sym)

						# Is nonterminal?
						else:
							res = apply(sym, pos)

							if res.res is None:
								break

							pos = res.pos

							if sym in self.emits.keys():
								seq.append(Node(sym, children = res.res))
							elif isinstance(res.res, Node):
								seq.append(res.res)
							elif isinstance(res.res, list):
								seq += res.res

						sym = None

					if not sym:
						pos = scanwhitespace(s, pos)

						# Insert production-based node?
						if (nterm, count) in self.emits.keys():
							seq = [Node(nterm, rule = count, children = seq)]

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
					if res is None or pos <= entry.pos:
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
				if entry.res is None:
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
				self.error(s, last)

			return None

		if self.goal in self.emits.keys():
			return Node(self.goal, children = ast.res)

		return ast.res

	def traverse(self, node, prePrefix = "pre_", passPrefix = "pass_", postPrefix = "post_", *args, **kwargs):
		"""
		Generic AST traversal function.

		This function allows to walk over the generated abstract syntax tree created by :meth:`pynetree.Parser.parse`
		and calls functions before, by iterating over and after the node are walked.

		:param node: The tree node to print.
		:param prePrefix: Prefix for pre-processed functions, named prePrefix + symbol.
		:param passPrefix: Prefix for functions processed by passing though children, named passPrefix + symbol.
		:param postPrefix: Prefix for post-processed functions, named postPrefix + symbol.
		:param args: Arguments passed to these functions as *args.
		:param kwargs: Keyword arguments passed to these functions as **kwargs.
		"""
		if node is None:
			return

		if isinstance(node, Node):

			# Pre-processing function
			fname = "%s%s" % (prePrefix, node.symbol)
			if fname and fname in dir(self) and callable(getattr(self, fname)):
				getattr(self, fname)(node, *args, **kwargs)

			for cnt, i in enumerate(node.children):
				self.traverse(i, prePrefix, passPrefix, postPrefix, *args, **kwargs)

				# Pass-processing function
				fname = "%s%s" % (passPrefix, node.symbol)
				if fname and fname in dir(self) and callable(getattr(self, fname)):
					getattr(self, fname)(node, _loopIndex = cnt, *args, **kwargs)
				else:
					fname = "%s%s_%d" % (passPrefix, node.symbol, cnt)

					if fname and fname in dir(self) and callable(getattr(self, fname)):
						getattr(self, fname)(node, *args, **kwargs)

			# Post-processing function
			fname = "%s%s" % (postPrefix, node.symbol)
			if fname and fname in dir(self) and callable(getattr(self, fname)):
				getattr(self, fname)(node, *args, **kwargs)

			# Allow for post-process function in the emit info.
			elif callable(self.emits[node.symbol]):
				self.emits[node.symbol](node, *args, **kwargs)

			elif self.emits[node.symbol]:
				print(self.emits[node.symbol])

		elif isinstance(node, list):
			for item in node:
				self.traverse(item, prePrefix, passPrefix, postPrefix, *args, **kwargs)

		else:
			raise ValueError()

	def dump(self, node, level = 0):
		if node is None:
			return

		if isinstance(node, Node):
			print("%s%s" % (level * " ", str(node)))

			for child in node.children:
				self.dump(child, level + 1)

		elif isinstance(node, list):
			for item in node:
				self.dump(item)

		else:
			raise ValueError()

if __name__ == "__main__":

	class Calculator(Parser):
		stack = []

		def post_INT(self, node):
			self.stack.append(float(node.match))

		def post_add(self, node):
			self.stack.append(self.stack.pop() + self.stack.pop())

		def post_sub(self, node):
			x = self.stack.pop()
			self.stack.append(self.stack.pop() - x)

		def post_mul(self, node):
			self.stack.append(self.stack.pop() * self.stack.pop())

		def post_div(self, node):
			x = self.stack.pop()
			self.stack.append(self.stack.pop() / x)

		def post_calc(self, node):
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
	calc.ignore(r"\s+")

	calc.emit("INT")
	calc.emit("mul")
	calc.emit("div")
	calc.emit("add")
	calc.emit("sub")
	calc.emit("calc")

	# Parse into a parse tree
	ast = calc.parse("1 + 2 * ( 3 + 4 ) * 5 - 6 / 7")

	print("--- abstract syntax tree ---")
	calc.dump(ast)

	# Traverse (interpret) the parse tree
	print("--- traversal ---")
	calc.traverse(ast)
