#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
pynetree: A light-weight parsing toolkit written in pure Python.
"""

__version__ = "0.6"
__license__ = "MIT"
__status__ = "Beta"
__author__ = "Jan Max Meyer"
__copyright__ = "Copyright 2015-2017 by Jan Max Meyer, Phorward Software Technologies"

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

class ParseError(Exception):
	def __init__(self, s, offset):
		row = s.count("\n", 0, offset) + 1
		col = s.rfind("\n", 0, offset)
		col = (offset + 1) if col < 1 else offset - col

		super(ParseError, self).__init__(
			"Parse error at line %d, column %d: >%s<" % (row, col, s[offset:]))

		self.offset = offset
		self.line = row
		self.column = col

class Node(object):
	"""
	This is an AST node.
	"""

	def __init__(self, symbol = None, emit = None, match = None, rule = None, children = None):
		self.symbol = symbol
		self.emit = emit
		self.rule = rule
		self.key = self.symbol if self.rule is None \
					else (self.symbol, self.rule)

		self.match = match
		self.children = children or []

	def __str__(self):
		s = self.emit or self.symbol or ""

		if self.rule is not None:
			s += "[%d]" % self.rule

		if not self.children and self.match is not None:
			s += " (%s)" % self.match

		return s

	def check(self, symbol):
		return self.symbol == symbol

	def contains(self, symbol):
		return bool(self.select(symbol, 0))

	def select(self, symbol, idx = -1):
		"""
		Select children by symbol from the current node.

		:param symbol: Symbol to be matched.
		:param idx: The desired index of the symbol.
		:return: If idx is < 0, the function returns a list of children matching symbol, else it returns the
					child at position `idx` that matches `symbol`. It returns None if there is no child.
		"""
		if idx < 0:
			return [child for child in self.children if child.symbol == symbol]

		for child in self.children:
			if child.symbol == symbol:
				if idx == 0:
					return child

				idx -= 1

		return None

	def dump(self, level=0):
		if self.symbol or self.emit:
			print("%s%s" % (level * " ", str(self)))
			level += 1

		for child in self.children:
			child.dump(level)

class Parser(object):
	"""
	The main parser class that implements a pynetree parser.

	The class provides functions for defining the grammar,
	parsing input, dumping and traversing the resulting parse
	tree or abstract syntax tree.
	"""
	AUTOTOKNAME = "T$%03d"

	def __init__(self, grm, dump = False):
		"""
		Constructs a new pynetree Parser object.

		:param grm: The grammar to be used; This can either be a dictionary of
					symbols and relating productions, or a string that is
					expressed in the BNF-styled grammar definition parser.
		:type grm: dict | str

		:param dump: Dump parsed grammar (only when grm was a string)
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
			# Rewrite grammar modifiers and goal according provided grammar
			for n, np in grm.items():
				if n.startswith("@"):
					n = n[1:]
					self.emits[n] = None

				if n.endswith("$"):
					if n in self.emits.keys():
						self.emits[n[:-1]] = self.emits[n]
						del self.emits[n]

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
						if len(sym) > 1 and sym.startswith("@"):
							sym = sym[1:]
							self.emits[sym] = None

						if any([len(sym) > 1 and sym.endswith(x)
						                            for x in "*+?"]):
							sym = generateModifier(n, sym[:-1], sym[-1:])

						rp.append(sym)

					rnp.append(rp)

				self.grammar[n] = rnp
		else:
			# Construct a parser for the BNF input language.
			bnfparser = Parser({
				"opt_ident": ["IDENT", ""],
				"opt_emit": ["EMIT", ""],

				"inline": ["EMIT opt_ident ( alternation )", "( alternation )"],

				"symbol": ["IDENT", "STRING", "TOKEN", "REGEX", "CCL", "inline"],

				"mod_kleene": "symbol *",
				"mod_positive": "symbol +",
				"mod_optional": "symbol ?",
				"modifier": ["mod_kleene", "mod_positive", "mod_optional", "symbol"],

				"sequence": ["sequence modifier", "modifier"],

				"production": ["sequence", ""],

				"alternation": ["alternation | production", "production"],

				"nontermflag": ["GOAL"], #fixme sticky
				"nontermflags": ["nontermflags nontermflag", "nontermflag", ""],
				"nontermdef": ["opt_emit IDENT nontermflags : alternation ;" ],

				"termsym": ["STRING", "REGEX", "CCL", "IDENT"],
				"termdef": ["opt_emit IDENT termsym ;", "IGNORE termsym ;"] ,

				"definition": ["nontermdef", "termdef"],
				"definitions": ["definitions definition", "definition"],
				"grammar$": "definitions"})

			bnfparser.ignore(r"\s+")
			bnfparser.ignore(r"//[^\n]*\n")
			bnfparser.ignore(r"/\*([^*]|\*[^/])*\*/")

			bnfparser.token("IDENT", r"\w+")
			bnfparser.token("CCL", r"\[[^\]]*\]")
			bnfparser.token("STRING", r"'[^']*'")
			bnfparser.token("TOKEN", r'"[^"]*"')
			bnfparser.token("REGEX", r"/(\\.|[^\\/])*/")

			bnfparser.token("GOAL", "$", static=True)
			bnfparser.token("EMIT", "@", static=True)
			bnfparser.token("IGNORE", r"%(ignore|skip)")

			bnfparser.emit(["IDENT", "STRING", "TOKEN", "REGEX", "CCL",
							"GOAL", "EMIT", "IGNORE"])
			bnfparser.emit(["inline", "mod_kleene", "mod_positive",
			                    "mod_optional", "production", "nontermdef",
									"termdef", "grammar"])

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
					buildNonterminal(sym, symdef.select("production"))

					if symdef.select("EMIT"):
						ident = symdef.select("IDENT", 0)
						if ident is not None:
							self.emit(sym, ident.match)
						else:
							self.emit((nonterm, len(self.grammar[nonterm])))

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

			def buildNonterminal(nonterm, prods):
				"""
				AST traversal function for nonterminals in the BNF-grammar.
				"""
				for p in prods:
					seq = []

					for s in p.children:
						seq.append(buildSymbol(nonterm, s))

					self.grammar[nonterm].append(seq)

			if dump:
				bnfparser.dump(ast)

			# Integrate all non-terminals into the grammar.
			for d in ast.select("nontermdef"):
				sym = d.select("IDENT", 0).match
				self.grammar[sym] = []

			# Now build the grammar
			nonterm = None

			for d in ast.children:
				if d.check("termdef"):
					term = d.select("IDENT", 0)
					if term:
						term = term.match
					else:
						term = self.AUTOTOKNAME % (len(self.tokens.keys()) + 1)

					if d.contains("STRING"):
						dfn = d.select("STRING", 0).match[1:-1]
					elif d.contains("REGEX"):
						dfn = re.compile(d.select("REGEX", 0).match[1:-1])
					elif d.contains("CCL"):
						dfn = re.compile(d.select("CCL", 0).match)
					else:
						dfn = d.select("IDENT", 1).match

					if term in self.tokens.keys():
						raise MultipleDefinitionError(term)

					self.tokens[term] = dfn

					if d.select("EMIT"):
						self.emit(term)
					elif d.select("IGNORE"):
						self.ignores.append(term)

				else: # d == "nontermdef"
					nonterm = d.select("IDENT", 0).match
					buildNonterminal(nonterm, d.select("production"))

					if d.select("EMIT"):
						self.emit(nonterm)
					if d.select("GOAL"):
						self.goal = nonterm

			# Last nonterminal becomes goal, if not set by flags
			if not self.goal and nonterm:
				self.goal = nonterm

		if not self.goal:
			raise GoalSymbolNotDefined()

		#print(self.grammar)
		#print(self.tokens)
		#print(self.emits)


	def token(self, name, token = None, static = False, emit = None):
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

		:param emit: If set, the token is configured to be emitted.
		:type emit: bool | str | callable
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

		if emit:
			self.emits[name] = emit if not isinstance(emit, bool) else None

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

	def emit(self, name, emit = None):
		"""
		Defines which symbols of the grammar shall be emitted in the
		generated, abstract syntax tree (AST).

		:param name: The name of the symbol that shall be emitted.
			Alternatively, a list of symbol names is accepted.
		:type name: str | list

		:param emit: An emit string that is used instead of the symbol
						name. This can also be a callable, which is
						called using AST traversal. If omitted, the
						symbol's name is used as emit.
		:type action: str | callable
		"""
		if isinstance(name, list):
			for n in name:
				self.emit(n, emit)

			return

		if isinstance(name, tuple):
			testname = name[0]
		else:
			testname = name

		if (not testname in self.grammar.keys()
			and not testname in self.tokens.keys()):
			raise SymbolNotFoundError(testname)

		self.emits[name] = emit

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
								seq.append(Node(sym, self.emits[sym],
								                s[pos:pos + res]))

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

							if sym in self.emits.keys():
								seq.append(Node(sym, self.emits[sym],
								                s[pos:pos + res.pos],
								                children = res.res))
							elif isinstance(res.res, Node):
								seq.append(res.res)
							elif isinstance(res.res, list):
								seq += res.res

							pos = res.pos

						sym = None

					if not sym:
						pos = scanwhitespace(s, pos)

						# Insert production-based node?
						if (nterm, count) in self.emits.keys():
							seq = [Node(nterm, self.emits[(nterm, count)], rule = count, children = seq)]

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

			raise ParseError(s, last)

		if self.goal in self.emits.keys():
			return Node(self.goal, self.emits[self.goal], children = ast.res)

		return Node(children=ast.res) #Return an empty node with children.

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
		def perform(prefix, loop = None, *args, **kwargs):
			if not (node.emit or node.symbol):
				return False

			if loop is not None:
				kwargs["_loopIndex"] = loop

			for x in range(0, 2):
				if x == 0:
					fname = "%s%s" % (prefix, node.emit or node.symbol)
				else:
					if node.rule is None:
						break

					fname = "%s%s_%d" % (prefix, node.emit or node.symbol, node.rule)

				if fname and fname in dir(self) and callable(getattr(self, fname)):
					getattr(self, fname)(node, *args, **kwargs)
					return True

				elif loop is not None:
					fname += "_%d" % loop

					if fname and fname in dir(self) and callable(getattr(self, fname)):
						getattr(self, fname)(node, *args, **kwargs)
						return True

			return False

		# Pre-processing function
		perform(prePrefix, *args, **kwargs)

		# Run through the children.
		for count, i in enumerate(node.children):
			self.traverse(i, prePrefix, passPrefix, postPrefix, *args, **kwargs)

			# Pass-processing function
			perform(passPrefix, loop=count, *args, **kwargs)

		# Post-processing function
		if not perform(postPrefix, *args, **kwargs):

			# Allow for post-process function in the emit info.
			if callable(self.emits[node.key]):
				self.emits[node.key](node, *args, **kwargs)

			# Else, just dump the emitting value.
			elif self.emits[node.key]:
				print(self.emits[node.key])

def main():
	import argparse, sys

	ap = argparse.ArgumentParser(
		description="pynetree - a light-weight parsing toolkit written in Python.",
		epilog="'grammar' and 'input' can be either supplied as strings or files.")

	ap.add_argument("grammar", type=str, help="Grammar to create a parser from.")
	ap.add_argument("input", type=str, nargs="*", help="Input to be processed by the parser.")

	ap.add_argument("-d", "--debug", help="Verbose, and print debug output", action="store_true")
	ap.add_argument("-v", "--verbose", help="Print processing information during run", action="store_true")
	ap.add_argument("-V", "--version", action="version", version="pynetree %s" % __version__)

	args = ap.parse_args()
	verbose = args.verbose or args.debug

	# Try to read grammar from a file.
	try:
		f = open(args.grammar, "rb")
		gfile = args.grammar

		if verbose:
			print("Reading grammar from '%s'" % gfile)

		grammar = f.read()
		f.close()

	except IOError:
		gfile = "grammar"
		grammar = args.grammar

	try:
		p = Parser(grammar, args.debug)

	except ParseError as e:
		print(("%s: " % gfile) + str(e))
		sys.exit(1)

	cnt = 0
	hasInput = bool(args.input)

	while True:
		ifile = "input.%d" % cnt
		cnt += 1

		if hasInput:
			if not args.input:
				break

			input = args.input.pop(0)

			# Try to read input from a file.
			try:
				f = open(input, "rb")
				ifile = input

				input = f.read()
				f.close()

			except IOError:
				pass

		else:
			if verbose:
				sys.stdout.write("> ")

			try:
				input = raw_input()
			except NameError:
				input = input()

			if not input:
				break

		try:
			ast = p.parse(input)

			if verbose:
				print("%s: Parsing successful" % ifile)

		except ParseError as e:
			print(("%s: " % ifile) + str(e))
			ast = None

		if ast:
			ast.dump()

if __name__ == "__main__":
	main()
