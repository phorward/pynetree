**pynetree**: *A light-weight parsing toolkit written in pure Python*

![Image of a Tree](pine.jpg)

# About

**pynetree** is both a Python library and a command-line utility for parsing.

Parsing is the process of transferring input matching a particular grammar, like e.g. a program source code, into a well-formed data structure. This data structure is a so called abstract syntax tree (AST).  pynetree is a tool doing all this for you: It takes a grammar description, runs a parser on provided input and generates the abstract syntax tree on a successful parse. This AST can than be taken to perform subsequent tasks, like writing an interpreter, compiler or any other kind of software requiring a parser.

The following Python example using pynetree defines a simple two-function calculator as an expression language, runs a parser on it, and dumps out the generated abstract syntax tree.
	
```python
import pynetree

p = pynetree.Parser("""
	%skip /\s+/;
	@int /\d+/;

	factor: int | '(' expr ')';

	@mul: term '*' factor;
	term: mul | factor;

	@add: expr '+' term;
	expr$: add | term;
""")

p.parse("1 + 2 * ( 3 + 4 ) * 5").dump()
```

When this program is run from a console, a proper abstract syntax tree will
be generated and printed, which shows the hierarchical structure of the parsed
expression.

```
add
 int (1)
 div
  mul
   int (2)
   add
    int (3)
    int (4)
  int (5)
```

pynetree also provides a handy command-line tool to rapidly prototype grammars. The next command just generates the same parser as the example program from above.

```
$ ./pynetree.py "@int /[0-9]+/; f: int | '(' e ')'; t: @mul( t '*' f ) | f; e: @add( e '+' t ) | t;" 
```

# Requirements

pynetree is written in pure Python. It runs natively with any Python >= 2.5.

The only import done so far is the build-in `re` module for regular expression support. Nothing more is required!

# Features

pynetree so far provides

- A top-down packrat parser with support of direct and indirect left recursive grammars.
- Mostly linear parsing time, even for left-recursive grammars due a powerful memorization algorithm.
- Grammars can be expressed as dict objects or by a BNF-grammar.
- Support functions for generating and traversing abstract syntax trees (AST).
- Lexical analysis can be performed via regular expressions (re), string or by Python callables.

Please check out http://pynetree.org to get help and the newest updates on the pynetree project.

The pynetree project is under heavy development, so that changes in API, function names, syntax or semantics may occur and need existing projects to be ported.

It has been developed in the course of implementing a top-down parser supporting left-recursive grammars. Therefore, pynetree is a parser that implements a modified version of the packrat parsing algorithm, but with the approach to provide true BNF-styled grammars, as known from other parser development tools and frameworks.

# Getting started

pynetree is not a parser generator in classic terms like yacc or bison. It
can be seen as a library to directly express and parse the desired grammar
within Python code.

## Command-line interface

Nevertheless, a command-line interface is provided for rapidly grammar
prototyping and testing.

```
usage: pynetree.py [-h] [-d] [-v] [-V] grammar [input [input ...]]

pynetree - a light-weight parsing toolkit written in Python.

positional arguments:
  grammar        Grammar to create a parser from.
  input          Input to be processed by the parser.

optional arguments:
  -h, --help     show this help message and exit
  -d, --debug    Verbose, and print debug output
  -v, --verbose  Print processing information during run
  -V, --version  show program's version number and exit

'grammar' and 'input' can be either supplied as strings or files.
```

## Using it as a library

For using pynetree in a Python script, it simply is required to create an object of the class `pynetree.Parser`.

The Parser class requires a BNF-grammar to describe the language that shall be parsed as parameter. This grammar can be expressed in two different ways:

1. 	As dict specifying the non-terminals as keys and their left-hand sides as the values (where the left-hand sides can be provided as list of strings). This requires much more configuration on the parsers token and emitting behavior, but is the Python-specific way.

2.  The other, more flexible method for specifying a grammar is pynetree's own grammar definition language, which itself internally is implemented using pynetree.

	This language is oriented on the classic BNF-style, but supports several syntactical elements to quickly define a language and its behavior for token definition and abstract syntax tree (AST) construction.

After the grammar is generally defined, the parser can be fine-tuned or extended to various features.

- `pynetree.Parser.token()` is used to define named terminal symbols, which can be regular expression patterns, static strings or callables.
- `pynetree.Parser.ignore()` is used for the definition of whitespace tokens, which are generally allowed between all other tokens.
- `pynetree.Parser.emit()` is used to define symbols (both non-terminal or terminal) that are emitted as nodes in AST. Terminal symbols will always define leafs in the AST, where non-terminals can emit leafs if no sub-ordered symbols are emitted. (In a full parse tree, non-terminals will never be leafs, but nodes).

The final parsing of a string is performed by the function `Parser.parse()`. This function returns the AST for the parsed input. AST are consisting of `pynetree.Node` objects or - in case of a sequence of multiple elements in the same level - lists of `pynetree.Node` objects.

To walk on such an AST, the function `pynetree.Node.dump()` can be used to print the AST in a well-formatted style, or `pynetree.Parser.traverse()` to possible call emitting functions on every node. It is also helpful to use these functions as templates for other, more specialized tree traversal and walker functions.

- `pynetree.Parser.parse()` parses an input string on the given grammar and returns and AST. The AST is represented as a hierarchy of `pynetree.Node` objects.
- `pynetree.Node.dump()` allows for dumping ASTs returned by `pynetree.Parser.parse()` in a well-formed style.
- `pynetree.Parser.traverse()` walks along an abstract syntax tree generated by `pynetree.Parser.parse()`, and performs function calls to perform top-down, pass-by and bottom-up tree traversal possibilities.

When higher AST traversal features are required for a pynetree parser, it is recommended to sub-class `pynetree.Parser` into a more specific class, serving as some kind of compiler or interpreter, like this example:

```python
import pynetree

class Calculator(pynetree.Parser):
	stack = []

	def __init__(self):
		super(Calculator, self).__init__(
			"""
			%ignore /\s+/;
			@INT    /\d+/;

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
```

Please do also take a look at the many examples provided with pynetree to get familiar with these functions and possibilities.

# Author

pynetree is developed and maintained by Jan Max Meyer, Phorward Software Technologies.

pynetree is the result of a several years experience in parser development tools, and is currently worked out as some kind of sister-project of the [Phorward Toolkit/libphorward](https://github.com/phorward/phorward), a  parsing a lexical analysis toolkit implementing LR/LALR parsers and focusing on the C programming language. Therefore, the BNF-styled grammar definition language of both pynetree and libphorward are similar and provide the same interface for both parser development tools.

# License

Copyright (C) 2015-2017 by Jan Max Meyer, Phorward Software Technologies.

You may use, modify and distribute this software under the terms and conditions of the MIT license. The full license terms are provided in the LICENSE file.

THIS SOFTWARE IS PROVIDED BY JAN MAX MEYER (PHORWARD SOFTWARE TECHNOLOGIES) AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL JAN MAX MEYER (PHORWARD SOFTWARE TECHNOLOGIES) BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
