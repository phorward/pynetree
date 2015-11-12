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

	tokens = {}
	actions = {}

	AFTER = 0
	BEFORE = 1
	ITERATE = 2

	def __init__(self, grm, goal):
		if not goal in grm.keys():
			raise SymbolNotFoundError(goal)

		# Check for correct productions
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

	def addToken(self, name, regex):
		if name in self.tokens.keys() or name in self.grm.keys():
			raise MultipleDefinitionError(name)

		self.tokens[name] = regex

	def addAction(self, name, func = None, kind = AFTER):
		self.actions[name] = (kind, func)

	def parse(self, s):

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
							res = re.match(self.tokens[sym], s[pos:])
							if not res:
								break

							seq.append((sym, s[pos : pos + len(res.group(0))]))
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
		if not ast:
			return None

		return (self.goal, ast.res)

	def __callaction(self, item, kind):
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
			self.__callaction(ast, self.BEFORE)

			if isinstance(ast[1], list):
				self.traverse(ast[1])

			self.__callaction(ast, self.AFTER)
		else:
			for i in ast:
				self.traverse(i)
				self.__callaction(ast, self.ITERATE)

	def dump(self, ast, level = 0):
		if ast is None:
			return

		if isinstance(ast, tuple):
			if isinstance(ast[1], list):
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
		#"term": ["mul", "factor"],
		"add": "expr + term",
		"sub": "expr - term",
		"expr": ["add", "sub", "term"],
		#"expr": ["add", "term"],
		"calc": "expr"
	}

	# TEST
	#g = { "x": "expr", "expr": ["x - INT", "INT"]}
	#i.addToken("IDENT", r"\w+")

	i = Interpreter(g, "calc")
	i.addToken("INT", r"\d+")
	i.addAction("INT", i.push)
	i.addAction("mul", i.mul)
	i.addAction("div", i.div)
	i.addAction("add", i.add)
	i.addAction("sub", i.sub)
	i.addAction("calc", i.result)

	i.dump(i.parse("1+2* (3+   4)*5-6/7"))
	i.traverse(i.parse("1+2*(3+4)*5-6   /7"))

