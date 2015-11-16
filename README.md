
DESCRIPTION
===========

pyParse is a simple, light-weight parsing toolkit for Python.

The toolkit has been developed in the course of implementing a top-down parser supporting left-recursive grammars. Therefore, pyParse is a parser that implements a modified version of the well-known packrat parsing algorithm, but with the approach to provide true BNF-styled grammars, as known from other parsing frameworks.

The following example already defines a simple grammar and runs a parser on the input "1+2*(3+4)+5":

	from pyparse import Parser

	p = Parser({
		"factor": ["INT", "( expr )"],
		"mul": "term * factor",
		"div": "term / factor",
		"term": ["mul", "div", "factor"],
		"add": "expr + term",
		"sub": "expr - term",
		"expr": ["add", "sub", "term"],
		"calc$": "expr"
	})

	p.addToken("INT", r"\d+")

	p.addAction("INT")
	p.addAction("mul")
	p.addAction("div")
	p.addAction("add")
	p.addAction("sub")
	p.addAction("calc")

	p.dump(p.parse("1 + 2 * (3 + 4) + 5"))


When this is ran from the console, a proper abstract syntax tree is printed:

	calc
	  add
		add
		  INT (1)
		  mul
			INT (2)
			add
			  INT (3)
			  INT (4)
		INT (5)


Grammars may also be expressed in a libphorward-similar BNF-like definition language, including AST construction information:

	p = Parser("$INT /\\d+/ %emit;"
			   "f: INT | '(' e ')';"
			   "mul %emit: t '*' f;"
			   "div %emit: t '/' f;"
			   "t: mul | div | f;"
			   "add %emit: e '+' t;"
			   "sub %emit: e '-' t;"
			   "e %goal: add | sub | t;")

	p.dump(p.parse("1 + 2 * (3 + 4) + 5"))

Above two instructions generate exactly the same output like above.

The pyParse toolkit is currently under heavy development, so changes in the function names and syntax may occur and follow. Have fun!


FEATURES
========

The parsing toolkit so far provides

- A top-down packrat parser with support of direct and indirect left recursive grammars
- Mostly linear parsing time, even for left-recursive grammars
- Grammars can be expressed as dict objects or parsed from a BNF grammar
- Functions for abstract syntax tree (AST) definition and traversion
- Lexical analysis is performed via regular expressions (re), string or as callables

Please check out https://bitbucket.org/codepilot/pyparse to get the newest updates on pyParse.


AUTHOR
======

The Phorward Toolkit is developed and maintained by Jan Max Meyer, Phorward Software Technologies.

It is the result of a several years experience in parser development systems, and is currently some kind of sub-project from a C-library called libphorward (https://bitbucket.org/codepilot/phorward). Therefore, the BNF-styled grammar definition language of both pyParse and libphorward are similar.

Help of any kind to extend and improve this product is always appreciated.


LICENSING
=========

Copyright (C) 2015 by Phorward Software Technologies, Jan Max Meyer.

You may use, modify and distribute this software under the terms and conditions of the MIT license. The full license terms can be obtained from the file LICENSE.

THIS SOFTWARE IS PROVIDED BY JAN MAX MEYER (PHORWARD SOFTWARE TECHNOLOGIES) AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL JAN MAX MEYER (PHORWARD SOFTWARE TECHNOLOGIES) BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

