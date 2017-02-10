# -*- coding: utf-8 -*-
from pynetree import Parser

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
	"factor": ["@INT", "( expr )"],
	"@mul": "term * factor",
	"@div": "term / factor",
	"term": ["mul", "div", "factor"],
	"@add": "expr + term",
	"@sub": "expr - term",
	"expr": ["add", "sub", "term"],
	"@calc$": "expr"
}

calc = Calculator(g)
calc.token("INT", r"\d+")
calc.ignore(r"\s+")

# Parse into a parse tree
ast = calc.parse("1 + 2 * ( 3 + 4 ) * 5 - 6 / 7")

print("--- abstract syntax tree ---")
calc.dump(ast)

# Traverse (interpret) the parse tree
print("--- traversal ---")
calc.traverse(ast)
