
DESCRIPTION
===========

pynetree is a simple, light-weight parsing toolkit for Python.

The toolkit has been developed in the course of implementing a top-down parser
supporting left-recursive grammars. Therefore, pynetree is a parser that
implements a modified version of the well-known packrat parsing algorithm, but
with the approach to provide true BNF-styled grammars, as known from other
parsing frameworks.

The following example already defines a simple grammar and runs a parser on
the input `1 + 2 * ( 3 + 4 ) + 5`:

	from pynetree import Parser

	p = Parser({
		"factor": ["INT", "( expr )"],
		"mul": "term * factor",
		"term": ["mul", "factor"],
		"add": "expr + term",
		"expr": ["add", "term"],
		"calc$": "expr"
	})

	p.ignore(r"\s+")
	p.token("INT", r"\d+")
	p.emit(["INT", "mul", "add"])

	p.dump(p.parse("1 + 2 * (3 + 4) + 5"))


When this program is ran from a console, a proper abstract syntax tree is
printed:

	add
	  add
		INT (1)
		mul
		  INT (2)
		  add
			INT (3)
			INT (4)
	  INT (5)


Grammars may also be expressed in pynetree's own BNF-styled grammar definition
language. This language allows to configure the entire parser behavor, including
token and whitespace symbol declaration and informations from which rules the
abstract syntax tree that is build during the parse process is constructed.
The following example code below produces exactly the same parser with the same
output as shown above, but all is defined within the grammar definition step.

	from pynetree import Parser

	p = Parser("""	$INT /\\d+/ %emit;
					$/\\s+/ %skip;
					f: INT | '(' e ')';
					mul: t '*' f %emit;
					t: mul | f;
					add: e '+' t %emit;
					e: add | t;""")

	p.dump(p.parse("1 + 2 * (3 + 4) + 5"))


The pynetree project is currently under heavy development, so changes in the
function names and syntax may occur and follow.

Have fun!


FEATURES
--------

The parsing toolkit so far provides

- A top-down packrat parser with support of direct and indirect
  left recursive grammars
- Mostly linear parsing time, even for left-recursive grammars
- Grammars can be expressed as dict objects or parsed from a BNF grammar
- Functions for abstract syntax tree (AST) definition and traversal
- Lexical analysis is performed via regular expressions (re), string or
  as call-ables

Please check out https://bitbucket.org/codepilot/pynetree to get the newest
updates on the pynetree project.


REQUIREMENTS
------------

pynetree is written in pure Python. It runs natively with Python 2 and 3.
The only import done so far is the build-in `re` module for regular expression
support.


GETTING STARTED
===============

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
	emitting behavior, but is the Python-specifc way.

2.	The other, more flexible method for specifying a grammar is pynetree's own
	grammar definition language, which itself internally is implemented using
	pynetree.

	This language is oriented on the classic BNF-style, but supports several
	syntactical elements to quickly define a language and its behavior for
	token definition and abstract syntax tree (AST) construction.

After the grammar is generally defined, the parser can be fine-tuned or extended
to various features.

- `Parser.token()` is used to define named terminal symbols, which can be
  regular expression patterns, static strings or callables.
- `Parser.ignore()` is used for the definition of whitespace tokens, which are
  generally allowed between all other tokens.
- `Parser.emit()` is used to define symbols (both non-terminal or terminal)
  that are emitted as nodes in AST. Terminal symbols will always define leafs
  in the AST, where non-terminals can emit leafs if no sub-ordered symbols are
  emitted. (In a full parse tree, non-terminals will never be leafs, but nodes).

The final parsing of a string is performed by the function `Parser.parse()`.
This function returns the AST for the parsed input. ASTs consist of tuples - or
in case of a sequence of multiple elements in the same level - lists of tuples,
where every tuple of a non-terminal results in

	("non-terminal", <child nodes>)

and every terminal results in

	("terminal", "parsed string that matched")

To walk on such an AST, the function `Parser.dump()` can be used to print the
AST in a well-formatted style, or `Parser.traverse()` to possible call emitting
functions on every node. It is also helpful to use these functions as templates
for other, more specialized tree traversal and walker functions.

Please take a look at the many examples to get familar with these functions and
possibilities.


AUTHOR
======

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


LICENSING
=========

Copyright (C) 2015, 2016 by Phorward Software Technologies, Jan Max Meyer.

You may use, modify and distribute this software under the terms and conditions
of the MIT license. The full license terms can be obtained from the file
LICENSE.

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
