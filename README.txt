# Lyps-Py
Lyps programming language - Implemented purely in Python 3.4

Lyps is intended as an toy interpreter for a very simple Lisp dialect.

Lyps is implemented entirely in python 3.4.

Goals
==========
Lisp-like syntax.
Macro-free.
Constant evaluation semantic. (Every expression is evaluated in exactly
   the same semantic.  Arguments are each evaluated in turn, then the
   results of theose evaulations are pushed onto the stack in reverse order).
The current implementation uses a tree-walking interpreter.  I expect this to change.

Uses
==========
Educational Only.
