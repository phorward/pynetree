
DESCRIPTION
===========

pynetree is a simple, light-weight parsing toolkit for and written in Python.

The toolkit has been developed in the course of implementing a top-down parser
supporting left-recursive grammars. Therefore, pynetree is a parser that
implements a modified version of the well-known packrat parsing algorithm, but
with the approach to provide true BNF-styled grammars, as known from other
parsing frameworks.

The following example already defines a simple grammar and runs a parser on
the input "1+2*(3+4)+5":

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


Grammars may also be expressed in a BNF-styled grammar definition language,
including AST construction information. The code below produces exactly the
same parser with the same output as shown above.

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
The only import done so far is the build-in `re` module for regular
expressions.

GETTING STARTED
===============

pynetree is not a parser generator in classic terms like yacc or bison. It
can be seen as a library to directly express and parse the desired grammar
within Python code.

To do this, it simply is required to create an object of the class
`pynetree.Parser`. The Parser class requires a BNF-grammar to describe the
language that shall be parsed as parameter. This grammar can be expressed
in two different ways:

1. 	As dict specifying the non-terminals als keys and their left-hand sides
	as the values (where the left-hand sides can be provided as list of strings)

	Example:

		p = Parser({"factor": "TOK",      # factor has one rule with a
										  # named terminal TOK, which has to
										  # be defined later.
					"expr$":              # expr has two rules, and is the goal
						["expr + factor",
						"expr - factor"]}

	Every left-hand side is split to its particular tokens, e.g. "expr", "+"
	and "term". If one token references another non-terminal or a defined
	token, this will be assumed, else the token is directly expected, like the
	"+" in this case.

	To handle tokens, whitespace, the AST traversal rules and more, calling
	subsequent functions of the Parser-class is required after a grammar has
	been specified in this way.

	For example, this must be done for the token INT, which should be the string
	"num":

		p.token("TOK", "num", static=True)

	And if we want to see expr and TOK in the ast, we have to call

		p.emit(["expr", "TOK"])

2.	The other, more flexible method for specifying a grammar is pynetree's own
	grammar definition language, which itself internally is implemented using
	pynetree.

	This language is oriented on the classic BNF-style, but supports several
	syntactical elements to quickly define a language and its behavior for
	token definition and AST traversal.

	Calling the constructor this way

		p = Parser("""
			$TOK 'num' %emit;
			factor: TOK;
			term %emit: expr '+' term | expr - term;""")

	and we are done: It produces exactly the same configuration like above.

	Some things to know about the grammar definition language:


AUTHOR
======

pynetree is developed and maintained by Jan Max Meyer and the company
Phorward Software Technologies.

This project is one result of a several years experience in parser development
systems, and is currently worked out as some kind of sub-project of a library
called libphorward, which is written in C and focuses on C program development.
See https://bitbucket.org/codepilot/phorward for more information.

Therefore, the BNF-styled grammar definition language of both pynetree and
libphorward are similar and should provide the same interface so far.

Help of any kind to extend and improve or enhance this product in any kind or
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
