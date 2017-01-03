![Image of a Tree](pine.jpg)

**pynetree**: *A light-weight parsing toolkit written in pure Python*
- Version: 0.4
- Release: beta

# DESCRIPTION #

pynetree is a simple, light-weight parsing toolkit for Python.

The toolkit has been developed in the course of implementing a top-down parser
supporting left-recursive grammars. Therefore, pynetree is a parser that
implements a modified version of the packrat parsing algorithm, but with the
approach to provide true BNF-styled grammars, as known from other parser
development tools and frameworks.

The following code example already defines a simple grammar and runs a parser
on the input `1 + 2 * ( 3 + 4 ) + 5`:

	from pynetree import Parser

	p = Parser({
		"factor": ["@INT", "( expr )"],
		"@mul": "term * factor",
		"@div": "term / factor",
		"term": ["mul", "div", "factor"],
		"@add": "expr + term",
		"@sub": "expr - term",
		"expr": ["add", "sub", "term"],
		"calc$": "expr"
	})

	p.ignore(r"\s+") #ignore whitespace
	p.token("INT", r"\d+")

	p.dump(p.parse("1 + 2 * (3 + 4) + 5"))


When this program is ran from a console, a proper abstract syntax tree will
be generated and printed:

	add
	  add
		INT (1)
		mul
		  INT (2)
		  add
			INT (3)
			INT (4)
	  INT (5)


Grammars may also be expressed in pynetrees self-hosted BNF-styled grammar
definition language. This language allows to configure the entire parser
behavior, including token and whitespace symbol declaration and information
from which rules the abstract syntax tree that is build during the parse
process is constructed.

The following example code below produces exactly the same parser with the same
output as shown above, but all is defined within the grammar definition step.

	from pynetree import Parser

	p = Parser("""	%skip /\\s+/;
					@INT /\\d+/;

					f: INT | '(' e ')';
					@mul: t '*' f;
					@div: t '/' f;

					t: mul | div | f;
					@add: e '+' t;
					@sub: e '-' t;

					e$: add | sub | t;
	""")

	p.dump(p.parse("123 + 456 * 789"))


The pynetree project is currently under heavy development, so that changes in
API, function names, syntax or semantics may occur and need existing projects
to be ported.

Have fun!


## FEATURES ##

The pynetree parser development toolkit so far provides

- A top-down packrat parser with support of direct and indirect
  left recursive grammars.
- Mostly linear parsing time, even for left-recursive grammars.
- Grammars can be expressed as dict objects or by a BNF-grammar.
- Support functions for generating and traversing abstract syntax trees (AST).
- Lexical analysis can be performed via regular expressions (re), string or
  by Python callables.

Please check out http://pynetree.org to get help and the newest updates on
the pynetree project.


## REQUIREMENTS ##

pynetree is written in pure Python. It runs natively with Python 2.x and 3.x.

The only import done so far is the build-in `re` module for regular expression
support. Nothing else is required!


# GETTING STARTED #

pynetree is not a parser generator in classic terms like yacc or bison. It
can be seen as a library to directly express and parse the desired grammar
within Python code.

To do this, it simply is required to create an object of the class
`pynetree.Parser`. The Parser class requires a BNF-grammar to describe the
language that shall be parsed as parameter. This grammar can be expressed
in two different ways:

1. 	As dict specifying the non-terminals as keys and their left-hand sides
	as the values (where the left-hand sides can be provided as list of
	strings). This requires much more configuration on the parsers token and
	emitting behavior, but is the Python-specific way.

2.	The other, more flexible method for specifying a grammar is pynetree's own
	grammar definition language, which itself internally is implemented using
	pynetree.

	This language is oriented on the classic BNF-style, but supports several
	syntactical elements to quickly define a language and its behavior for
	token definition and abstract syntax tree (AST) construction.

After the grammar is generally defined, the parser can be fine-tuned or extended
to various features.

- `pynetree.Parser.token()` is used to define named terminal symbols, which can
  be regular expression patterns, static strings or callables.
- `pynetree.Parser.ignore()` is used for the definition of whitespace tokens,
  which are generally allowed between all other tokens.
- `pynetree.Parser.emit()` is used to define symbols (both non-terminal or
  terminal) that are emitted as nodes in AST. Terminal symbols will always
  define leafs in the AST, where non-terminals can emit leafs if no sub-ordered
  symbols are emitted. (In a full parse tree, non-terminals will never be leafs,
  but nodes).

The final parsing of a string is performed by the function `Parser.parse()`.

This function returns the AST for the parsed input. AST are consisting of
`pynetree.Node` objects or - in case of a sequence of multiple elements in the
same level - lists of `pynetree.Node` objects.

To walk on such an AST, the function `pynetree.Parser.dump()` can be used to
print the AST in a well-formatted style, or `pynetree.Parser.traverse()` to
possible call emitting functions on every node. It is also helpful to use these
functions as templates for other, more specialized tree traversal and walker
functions.

- `pynetree.Parser.parse()` parses an input string on the given grammar.
- `pynetree.Parser.dump()` dumps an abstract syntax tree generated by
  `pynetree.Parser.parse()`.
- `pynetree.Parser.traverse()` walks along an abstract syntax tree generated by
  `pynetree.Parser.parse()`, and performs function calls to perform top-down,
   pass-by and bottom-up tree traversal possibilities.

When higher AST traversal features are required for a pynetree use-case, it is
recommended to sub-class the `pynetree.Parser`-class into an own class, which
could serve as some kind of compiler or interpreter, like here:

	import pynetree

	class Calculator(pynetree.Parser):
		stack = []

		def __init__(self):
			super(Calculator, self).__init__(
				"""
				%ignore /\\s+/;
				@INT    /\\d+/;

				f:      INT | '(' e ')';

				@mul:   t "*" f;
				@div:   t "/" f;
				t:      mul | div | f;

				@add:   e "+" t;
				@sub:   e "-" t;
				e:      add | sub | t;

				@calc$: e;
				""")

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

	c = Calculator()
	c.traverse(c.parse("1337 - 42 + 23"))


Please do also take a look at the many examples provided with pynetree to get
familiar with these functions and possibilities.


# AUTHOR #

pynetree is developed and maintained by Jan Max Meyer and the company
Phorward Software Technologies.

This project is one result of a several years experience in parser development
tools, and is currently worked out as some kind of sister-project of a library
called libphorward, that focuses on the C programming language. Therefore, the
BNF-styled grammar definition language of both pynetree and libphorward are
similar and should provide the same interface for both parser generation tools.
Take a look at https://bitbucket.org/codepilot/phorward for more information.

Help of any kind to extend and improve or enhance this project in any kind or
way is always appreciated.


# LICENSING #

Copyright (C) 2015-2017 by Phorward Software Technologies, Jan Max Meyer.

You may use, modify and distribute this software under the terms and conditions
of the MIT license. The full license terms are provided in the LICENSE file.

THIS SOFTWARE IS PROVIDED BY JAN MAX MEYER (PHORWARD SOFTWARE TECHNOLOGIES) AS
IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL JAN MAX MEYER (PHORWARD SOFTWARE TECHNOLOGIES) BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
