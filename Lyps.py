import math
import datetime
import fractions
import functools
import sys

# #################
# Lyps Function API
class LypsRuntimeError( Exception ):
   def __init__( self, *args ):
      super().__init__( self, *args )

def _lRuntimeError( fnName, error, usage=None ):
   if usage is None:
      errStr = "ERROR '{0}': {1}".format( fnName, error )
   else:
      errStr = "ERROR '{0}': {1}\nUSAGE: {2}".format( fnName, error, usage )

   raise LypsRuntimeError( errStr )

# Pything / Lyps Type Representation Mapping
L_NUMBER = (int,float,fractions.Fraction)
L_ATOM   = (int,float,fractions.Fraction,str)

def _lRuntimeError2( function, error ):
   if function.__lusage__ is None:
      _lRuntimeError( function.__lname__, error )
   else:
      _lRuntimeError( function.__lname__, error, usage=function.__lusage__ )

def _lEval( env, expr ):
   '''
   Evaluate expr as a lyps expression.
   Note:  Symbols (including function names) need to be in capitals before
   invoking this function.
   '''
   if isinstance( expr, L_ATOM ):
      return expr
   else:
      return expr.eval( env )

def _lEval2( env, *expr ):
   '''
   Evaluate expr as a lyps list expression.
   Note:  Symbols (including function names) need to be in capitals before
   invoking this function.
   '''
   expr = LList( *expr )
   return expr.eval( env )

def _lEval3( env, fnName, *args ):
   '''
   Evaluate fnName with the args provided.
   _lEval3 Quotes each arg to prevent further evaluation on them.
   Note:  Symbols (including function names) need to be in capitals before
   invoking this function.
   '''
   theExpr = [ LSymbol(fnName) ]
   for arg in args:
      theExpr.append( LList(LSymbol('QUOTE'), arg) )
   theExprList = LList( *theExpr )
   return theExprList.eval( env )

def _lTrue( expr ):
   return (expr is not LNULL) and (expr != 0)

L_STDOUT = sys.stdout
L_STDIN  = sys.stdin

# ##############################
# The Lyps Execution Environment
class LEnv( object ):
   PRMITIVE_LIST = [ ]
   GLOBAL_SCOPE  = None

   def __init__( self, parent=None ):
      self._parent = parent
      self._locals = { }
      
      if LEnv.GLOBAL_SCOPE is None:
         LEnv.GLOBAL_SCOPE = self
         self.reInitialize( )

   def reInitialize( self ):
      root = LEnv.GLOBAL_SCOPE
      root._parent = None
      root._locals = { name:value for name,value in LEnv.PRMITIVE_LIST }
      return root

   def defLocal( self, symStr, value ):
      if isinstance( symStr, LSymbol ):
         symStr = symStr._val
      
      self._locals[ symStr ] = value
      return value

   def defGlobal( self, symStr, value ):
      if isinstance( symStr, LSymbol ):
         symStr = symStr._val
      
      LEnv.GLOBAL_SCOPE._locals[ symStr ] = value
      return value

   def setValue( self, sym, value ):
      if isinstance( sym, LSymbol ):
         symStr = sym._val
      else:
         symStr = sym
      
      scope = self
      while scope is not None:
         if symStr in scope._locals:
            scope._locals[ symStr ] = value
            return value
         else:
            scope = scope._parent
      
      self._locals[ symStr ] = value
      return value
 
   def getValue( self, sym ):
      if isinstance( sym, LSymbol ):
         symStr = sym._val
      else:
         symStr = sym
      
      scope = self
      while scope is not None:
         try:
            return scope._locals[ symStr ]
         except:
            scope = scope._parent
      
      return sym

   def unset( self, sym ):
      if isinstance( sym, LSymbol ):
         symStr = sym._val
      else:
         symStr = sym
      
      scope = self
      while scope is not None:
         if symStr in scope._locals:
            del scope._locals[ symStr ]
         else:
            scope = scope._parent
      
      return sym

   def localSymbols( self ):
      return sorted( self._locals.keys() )
   
   def parentEnv( self ):
      return self._parent

   def openScope( self ):
      return LEnv( self )
   


# ###############################
# Lyps Runtime Object Definitions
class LSymbol( object ):
   def __init__( self, val ):
      self._val = val
   
   def __str__( self ):
      return self._val
   
   def __eq__( self, other ):
      try:
         return self._val == other._val
      except:
         return False

   def __ne__( self, other ):
      try:
         return self._val != other._val
      except:
         return True

   def eval( self, env ):
      try:
         return env.getValue( self )
      except:
         return self


class LList( object ):
   def __init__( self, *elements ):
      self._list = list(elements)

   def __getitem__( self, index ):
      return self._list[ index ]

   def __len__( self ):
      return len(self._list)
   
   def __iter__( self ):
      return iter( self._list )

   def __str__( self ):
      if self is LNULL:
         return 'NULL'
      
      resultStr = '('
      isFirst = True
      for mbr in self._list:
         if isFirst:
            isFirst = False
         else:
            resultStr += ' '
         
         if isinstance( mbr, str ):
            resultStr += '\"' + str(mbr) + '\"'
         else:
            resultStr += str(mbr)
      
      resultStr += ')'
      return resultStr

   def __eq__( self, other ):
      '''
      (defun!! '(equal? expr1 expr2)
               '(cond '( ((or (isAtom? expr1)    
                              (isNull? expr1))
                                       (= expr1 expr2))
                         ((and (isList? expr1)
                               (isList? expr2))
                                       (and (isList? expr2)
                                            (and (equal? (first expr1) (first expr2))
                                                 (equal? (rest expr1) (rest expr2)))))
                         (1
                                       null))))
      '''
      if not isinstance(other, LList):
         return False
   
      if len(self) != len(other):
         return False
      
      for subSelf, subOther in zip( self, other ):
         if subSelf != subOther:
            return False
      
      return True
   def copy( self ):
      return LList( *self._list[:] )

   def insert( self, index, value ):
      self._list.insert( index, value )

   def eval( self, env ):
      if len(self._list) == 0:
         return LNULL
      
      # The Function name
      try:
         fnName   = self._list[0]._val
         exprArgs = self._list[1:]
      except:
         raise LypsRuntimeError( 'Badly formed list expression - function name expected.' )

      if fnName == 'QUOTE':
         return self._list[1]
      
      # Evaluate each arg
      evaluatedArgs = [ ]
      evaluatedKeys = { }
      for argNum,argExpr in enumerate(exprArgs):
         try:
            evaluatedArg = _lEval( env, argExpr )
         except:
            raise LypsRuntimeError( 'Error evaluating list expression {0}, argument {1}.'.format(fnName,argNum+1) )
         
         evaluatedArgs.append( evaluatedArg )
      
      # Get the function definition
      try:
         fnDef = env.getValue( fnName )
      except:
         raise LypsRuntimeError( 'Symbol {0} is not the name of a function.'.format(fnName) )

      # Evaluate the top level function
      try:
         return fnDef( env, *evaluatedArgs, **evaluatedKeys )
      except TypeError as ex:
         raise LypsRuntimeError( 'Error evaluating list expression {0}.'.format(fnName) )

   def first( self ):
      return self._list[ 0 ]
   
   def rest( self ):
      if len(self._list) < 2:
         return LNULL
      else:
         return LList( *self._list[ 1 : ])

LNULL = LList( )
LEnv.PRMITIVE_LIST.append( ( 'NULL',  LNULL    ) )
LEnv.PRMITIVE_LIST.append( ( 'PI',    math.pi  ) )
LEnv.PRMITIVE_LIST.append( ( 'E',     math.e   ) )
LEnv.PRMITIVE_LIST.append( ( 'INF',   math.inf ) )
LEnv.PRMITIVE_LIST.append( ( '-INF', -math.inf ) )
LEnv.PRMITIVE_LIST.append( ( 'NAN',   math.nan ) )

class LMap( object ):
   def __init__( self, **mappings ):
      assert isinstance( mappings, dict )
      self._dict = mappings
   
   def __str__( self ):
      resultStr = '(MAP\n'
      for key in sorted(self._dict.keys( )):
         resultStr += '   ('
         resultStr += key + ' '
         resultStr += str(self._dict[key])
         resultStr += ')\n'
      resultStr += ')\n'
      return resultStr
   
   def __setitem__( self, key, val ):
      if isinstance( key, LSymbol ):
         self._dict[ key._val ] = val
      else:
         self._dict[ key ] = val

   def __getitem__( self, key ):
      if isinstance( key, LSymbol ):
         return self._dict[ key._val ]
      else:
         return self._dict[ key ]

   def get( self, key ):
      try:
         val = self._dict[ key ]
         return LList( LSymbol(key), val )
      except:
         return LNULL

   def eval( self, env ):
      return self

class LFunction( object ):
   def __init__( self, name, params, body ):
      self._name    = name
      self._params  = params
      self._body    = body
      
      self.setName( name )
   
   def __str__( self ):
      return self._nameStr
   
   def __call__( self, env, *args, **keys ):
      return self.eval( env, *args, **keys )

   def setName( self, name ):
      self._name = name
      paramList = [ x._val for x in self._params ]
      self._nameStr = "(Function '(" + self._name + " " + ' '.join(paramList) + ") ... )"
 
   def eval( self, env, *args, **keys ):
      env = env.openScope( )
      
      # store the arguments as locals
      for paramName, argVal in zip( self._params._list, args ):
         env.defLocal( paramName, argVal )
      
      expr = self._body
      
      if isinstance(expr, (int,float,str)):
         return expr
      else:
         return expr.eval( env )
   
class LPrimitive( object ):
   def __init__( self, fn ):
      self._fn = fn
   
   def __call__( self, env, *args, **keys ):
      return self._fn( env, *args, **keys )


class LDefPrimitive( object ):
   def __init__( self, primitiveSymbol, args=None ):
      self._name  = primitiveSymbol.upper( )
      if args is not None:
         self._usage = '({0} {1})'.format( primitiveSymbol, args )
      else:
         self._usage = None
   
   def __call__( self, primitiveDef ):
      lPrimitivObj = LPrimitive( primitiveDef )
      lPrimitivObj.__lname__  = self._name
      lPrimitivObj.__lusage__ = self._usage
      LEnv.PRMITIVE_LIST.append( (self._name,lPrimitivObj) )
      return lPrimitivObj


# ##########################
# Lyps Primitive Definitions
# ##########################

# =================
# Symbol Definition
# -----------------
@LDefPrimitive( 'def!', '\'<symbol> <object>' )  # (def! '<symbol> <expr> )  ;; Define a var in the local symbol table
def LP_defLocal( env, *args, **keys ):
   if len(args) != 2:
      _lRuntimeError2( LP_defLocal, '2 arguments expected.' )
   
   try:
      if isinstance( args[1], LFunction ):
         args[1].setName( args[0]._val )
   
      return env.defLocal( *args )
   except:
      _lRuntimeError2( LP_defLocal, 'Unknown error.' )

@LDefPrimitive( 'def!!', '\'<symbol> <object>' ) # (def!! '<symbol> <expr> ) ;; Define a var in the global symbol table
def LP_defGlobal( env, *args, **keys ):
   if len(args) != 2:
      _lRuntimeError2( LP_defGlobal, '2 arguments expected.' )
   
   try:
      if isinstance( args[1], LFunction ):
         args[1].setName( args[0]._val )
   
      return env.defGlobal( *args )
   except:
      _lRuntimeError( LP_defGlobal, 'Unknown error.' )
   
@LDefPrimitive( 'set!', '\'<symbol> <object>' )  # (set! '<symbol> <expr> )  ;; Set a variable.  If doesn't already exist make a local.
def LP_setLocal( env, *args, **keys ):
   if len(args) != 2:
      _lRuntimeError2( LP_setLocal, '2 arguments expected.' )
   
   try:
      if isinstance( args[1], LFunction ):
         args[1].setName( args[0]._val )
   
      return env.setValue( *args )
   except:
      _lRuntimeError2( LP_setLocal, 'Unknown error.' )

@LDefPrimitive( 'undef!', '\'<symbol>' )         # (undef! '<symbol>)   ;; undefine the most local definition for <name>
def LP_undef( env, *args, **keys ): 
   if len(args) != 1:
      _lRuntimeError2( LP_undef, '1 argument exptected.' )
   
   try:
      return env.unset( *args )
   except:
      _lRuntimeError2( LP_undef, 'Unknown error.' )

# ==================
# Control Structures
# ------------------
@LDefPrimitive( 'lam' )            # (lam '(<arg1> <arg2> ...) '<expr2>);; create an anon lambda function
def LP_lam( env, *args, **keys ):
   try:
      funcParams,funcBody = args
   except:
      _lRuntimeError( 'lam', '2 arguments expected.', usage='(lam \'(<arg1:symbol> <arg2:symbol> ...) \'<expr>)' )
   
   return LFunction( "", funcParams, funcBody )

@LDefPrimitive( 'recurse' )        # (recurs <arg1> <arg2> ...)         ;; have a (lam ...) call itself.
def LP_recurse( env, *args, **keys ):
   pass

@LDefPrimitive( 'block' )          # (block '(<expr1> <expr2> ...))     ;; execute the sequence of expr's in a nested scope
def LP_block( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'block', '1 argument expected.', usage='(block \'(<expr-1> <expr-2> ...) )' )
   
   env = env.openScope( )
   
   lastValue = LNULL
   for expr in args[0]:
      lastValue = _lEval( env, expr )
   
   return lastValue

@LDefPrimitive( 'if' )             # (if <cond> '<conseq> ['<alt>])     ;; If statement
def LP_if( env, *args, **keys ):
   numArgs = len(args)
   if not(2 <= numArgs <= 3):
      _lRuntimeError( 'if', '3 arguments expected.', usage='(if <cond> <thenPart:expr> [<elsePart:expr>])' )
   
   try:
      cond,*rest = args
      
      if _lTrue(cond):
         return _lEval( env, rest[0])    # The THEN part
      elif numArgs == 3:
         return _lEval( env, rest[1])    # The ELSE part
      else:
         return LNULL
   except:
      _lRuntimeError( 'if', 'Unknown error.', usage='(if <cond> <thenPart:expr> [<elsePart:expr>])' )

   if numArgs == 2:
      cond,conseq = args
      
      if _lTrue(cond):
         return _lEval( env, conseq )
      else:
         return LNULL
   else:
      cond,conseq,alt = args
      
      if _lTrue(cond):
         return _lEval( env, conseq )
      else:
         return _lEval( env, alt )

@LDefPrimitive( 'cond' )           # (cond '( (<cond> <expr>) (<cond> <expr>) ...))
def LP_cond( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'cond', '1 argument exptected.', usage='(cond \'( (<cond-1:expr> <body-1:expr>) (<cond-2:expr> <body-2:expr>) ...) )' )
   
   caseList = args[0]
   for caseNum,case in enumerate(caseList):
      try:
         testExpr,bodyExpr = case._list
      except:
         _lRuntimeError( 'cond', "Entry {0} does not contain a (<cond:expr> <body:expr>) pair.".format(caseNum+1) )
      
      if _lTrue(_lEval(env,testExpr)):
         return _lEval( env, bodyExpr )

   return LNULL

@LDefPrimitive( 'case' )           # (case <expr> '( (<val> <expr>) (<val> <expr>) ...))
def LP_case( env, *args, **keys ):          
   try:
      expr,caseList = args
   except:
      _lRuntimeError( 'case', '2 arguments exptected.', usage='(case <expr> \'( (<val-1> <expr-1>) (<val-2> <expr-2>) ...) )' )
   
   exprVal = _lEval( env, expr )
   
   for caseNum,case in enumerate(caseList):
      try:
         caseVal,caseExpr = case._list
      except:
         _lRuntimeError( 'case', "Entry {0} does not contain a (<val> <expr>) pair.".format(caseNum+1) )
      
      if _lEval(env,caseVal) == exprVal:
         return _lEval( env, caseExpr )
   
   return LNULL

@LDefPrimitive( 'quote' )          # (quote <expr>)                     ;; return <expr> without evaluating it
def LP_quote( env, *args, **keys ):         
   if (len(args) != 1):
      _lRuntimeError( 'quote', '1 argument exptected.', usage='(quote <expr>)' )
   
   return args[0]

@LDefPrimitive( 'eval' )           # (eval '<expr>)                     ;; evaluate <expr>
def LP_eval( env, *args, **keys ):
   if (len(args) != 1):
      _lRuntimeError( 'eval', '1 argument exptected.', usage='(eval <expr>)' )
   
   return _lEval( env, args[0] )

@LDefPrimitive( 'apply' )          # (apply <fn> <list>)                ;; apply fn to each member of list.  Return the results in a list.
def LP_apply( env, *args, **keys ):
   try:
      fnName,theList = args
   except:
      _lRuntimeError( 'apply', '2 arguments expected.', usage='(apply <fn:symbol> <list>)' )
   
   result = [ ]
   
   try:
      values = theList._list
   except:
      _lRuntimeError( 'apply', 'list expected for argument 2.' )
      
   if isinstance(fnName, LSymbol):
      fnNameStr = fnName._val
   else:
      fnNameStr = fnName
   
   # Get the function definition
   try:
      fnDef = env.getValue( fnNameStr )
   except:
      _lRuntimeError( 'apply', "Function name symbol expected for argument 1." )

   for valueNum,val in enumerate(values):
      # Evaluate the top level function
      try:
         rVal = fnDef( env, val )
         result.append( rVal )
      except TypeError as ex:
         _lRuntimeError( 'apply', "Error evaluating list expression {0}.".format(valueNum+1) )

   return LList( *result )

@LDefPrimitive( 'applyAndFlatten' )# (applyAndFlatten <fn> <list>)      ;; apply fn to each member of list.  Return the results in a list.
def LP_applyAndFlatten( env, *args, **keys ):
   try:
      fnName,theList = args
   except:
      _lRuntimeError( 'applyAndFlatten', '2 arguments expected.', usage='(applyAndFlatten <fn:symbol> <list>)' )

   result = [ ]
   
   try:
      values = theList._list
   except:
      _lRuntimeError( 'applyAndFlatten', 'list expected for argument 2.' )
   
   if isinstance(fnName, LSymbol):
      fnNameStr = fnName._val
   else:
      fnNameStr = fnName
   
   # Get the function definition
   try:
      fnDef = env.getValue( fnNameStr )
   except:
      _lRuntimeError( 'applyAndFlatten', "Function name symbol expected for argument 1." )

   for valueNum,val in enumerate(values):
      # Evaluate the top level function
      try:
         rVal = fnDef( env, val )
         result = result + rVal._list
      except TypeError as ex:
         _lRuntimeError( 'applyAndFlatten', "Error evaluating list expression {0}.".format(valueNum+1) )

   return LList( *result )

@LDefPrimitive( 'forEach' )        # (forEach <symbol> <list> <expr>)   ;; each iteration assigns list element to symbol, and evaluates expr.
def LP_forEach( env, *args, **keys ):
   try:
      symbol,lst,expr = args
   except:
      _lRuntimeError( 'forEach', '3 arguments expected.', usage='(forEach <symbol> <iterable:list> <body:expr>)' )
   
   if isinstance( symbol, LSymbol ):
      symbolStr = symbol._val
   else:
      symbolStr = symbol
   
   latestResult = LNULL
   for exprNum,subordinate in enumerate(lst):
      try:
         env.setValue( symbolStr, subordinate ) 
      except Exception as ex:
         _lRuntimeError( 'forEach', "Error evaluating list expression {0}.".format(exprNum+1) )
      
      try:
         latestResult = _lEval( env, expr )
      except Exception as ex:
         _lRuntimeError( 'ForEach', "Error evaluating body for list expression {0}.".format(exprNum+1) )
   
   return latestResult
   
   
# =======================
# List & Map Manipulation
# -----------------------
@LDefPrimitive( 'list' )           # (list <expr-1> <expr-2> ...)       ;; return a list of evaluated expressions
def LP_list( env, *args, **Keys ):
   if len(args) == 0:
      _lRuntimeError( 'list', '1 or more arguments expected.', usage='(list <expr-1> <expr-2> ...)' )

   theLst = [ ]
   
   for exprNum,expr in enumerate(args):
      try:
         theLst.append( expr )
      except Exception as ex:
         raise _lRuntimeError( 'Invalid argument {0}'.format(exprNum+1) )
   
   return LList( *theLst )

@LDefPrimitive( 'first' )          # (first <list>)                     ;; return the first item in the list
def LP_first( env, *args, **Keys ):
   if len(args) != 1:
      _lRuntimeError( 'first', '1 argument expected.', usage='(first <list>)' )
   
   theList = args[0]
   if len(theList) == 0:
      return LList()
   else:
      try:
         return theList.first()
      except:
         _lRuntimeError( 'first', 'Invalid argument.' )

@LDefPrimitive( 'rest' )           # (rest <list>)                      ;; return the list without the first item
def LP_rest( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'rest', '1 argument expected.', usage='(rest <list>)' )
   
   theList = args[0]
   if len(theList) < 2:
      return LList( )
   else:
      try:
         return theList.rest()
      except:
         _lRuntimeError( 'rest', 'Invalid argument.' )

@LDefPrimitive( 'cons' )           # (cons '<obj> '<list>)              ;; return the list with <obj> inserted into the front
def LP_cons( env, *args, **keys ):
   try:
      arg1,arg2 = args
   except:
      _lRuntimeError( 'cons', '2 arguments exptected.', usage='(cons <object> <list>)' )
   
   try:
      copiedList = arg2.copy( )
      copiedList.insert( 0, arg1 )
   except:
      _lRuntimeError( 'cons', 'Invalid argument.' )

   return copiedList

@LDefPrimitive( 'push!' )          # (push! '<listOrMap> [ '<keyOrIndex> ] '<value>)
def LA_Push( env, *args, **keys ):
   numArgs = len(args)
   if numArgs == 2:
      keyed = args[0]
      key   = 0
      value = args[1]
   elif numArgs == 3:
      keyed, key, value = args
   else:
      _lRuntimeError( 'push!', '2 or 3 arguments exptected.', usage='(push! <listOrMap> [<keyOrIndex>] <value>)' )
   
   if isinstance( key, LSymbol ):
      key = key._val
   
   try:
      if isinstance( keyed, LList ):
         if key == -1:
            keyed._list.append( value )
         else:
            keyed._list.insert( key, value )
      elif isinstance( keyed, LMap ):
         keyed._dict[ key ] = value
   except:
      _lRuntimeError( 'push!', 'Invalid argument.' )
   
   return keyed
   
@LDefPrimitive( 'pop!' )           # (pop! '<listOrMap> [ '<keyOrIndex> ] )
def LP_pop( env, *args, **keys ):
   numArgs = len(args)
   
   if numArgs == 1:
      keyed = args[0]
      key   = 0
   elif numArgs > 1:
      keyed, key = args
   else:
      _lRuntimeError( 'pop!', '1 or 2 arguments expected.', usage='(pop! <listOrMap> [<keyOrIndex>])' )
   
   if isinstance( key, LSymbol ):
      key = key._val
   
   try:
      value = keyed[ key ]
      del keyed[ key ]
   except:
      _lRuntimeError( 'pop!', 'Invalid argument.' )
   
   return value
   
@LDefPrimitive( 'at' )             # (at '<listOrMap> '<keyOrIndex>)
def LP_at( env, *args, **keys ):
   try:
      keyed,key = args
   except:
      _lRuntimeError( 'at', '2 arguments expected.', usage='(at <listOrMap> <keyOrIndex>)' )
   
   if isinstance( key, LSymbol ):
      key = key._val
   
   try:
      return keyed[ key ]
   except:
      _lRuntimeError( 'at', 'Invalid argument.' )

@LDefPrimitive( 'atSet!' )         # (atSet! <listOrMap> <keyOrIndex> <value>)
def LP_atSet( env, *args, **keys ):
   try:
      keyed,key,value = args
   except:
      _lRuntimeError( 'atSet!', '3 arguments expected.', usage='(atSet! <listOrMap> <keyOrIndex> <value>)' )
   
   if isinstance( key, LSymbol ):
      key = key._val
   
   try:
      keyed._dict[ key ] = value
   except:
      _lRuntimeError( 'atSet!', 'Invalid argument.' )
   
   return value

@LDefPrimitive( 'join' )           # (join '<list-1> '<list-2>)
def LP_join( env, *args, **keys ):
   try:
      arg1,arg2 = args
   except:
      _lRuntimeError( 'join', '2 arguments expected', usage='(join <list-1> <list-2>)' )
 
   if isinstance( arg1, list ) and isinstance( arg2, list ):
      return arg1 + arg2
   else:
      _lRuntimeError( 'join', 'Invalid argument.' )

@LDefPrimitive( 'hasValue?' )      # (hasValue? '<listOrMap> '<value>)
def LP_hasValue( env, *args, **keys ):
   try:
      aList,aVal = args
   except:
      _lRuntimeError( 'hasValue?', '2 arguments expected.', usage='(hasValue <listOrMap> <valueOrKey>)' )
   
   try:
      return 1 if aVal in aList._list else LNULL
   except:
      _lRuntimeError( 'hasValue?', 'Invalid argument.')
   
@LDefPrimitive( 'map' )            # (map '( (<key> <val>) (<key> <val>) ...))  ;; construct a map of key-value pairs
def LP_map( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'map', '1 argument exptected.', usage='(map \'( (<key-1 val-1) (key-2 val-2) ...) )' )
   
   theMapping = { }
   
   for entryNum,key_expr_pair in enumerate(args[0]._list):
      try:
         key,expr =  key_expr_pair
      except:
         _lRuntimeError( 'map', "Entry {0} does not contain a (key value) pair.".format(entryNum+1) )
      
      if isinstance( key, (int,float,str) ):
         theMapping[ key ] = _lEval( env, expr)
      elif isinstance( key, LSymbol ):
         theMapping[ key._val ] = _lEval( env, expr )
      else:
         raise _lRuntimeError( 'map', 'Entry {0} has an invalid <key> type.'.format(entryNum+1) )
   
   return LMap( **theMapping )

@LDefPrimitive( 'update!' )        # (update! <map1> <map2>)                    ;; merge map2's data into map1
def LP_update( env, *args, **keys ):
   try:
      map1,map2 = args
   except:
      _lRuntimeError( 'update!', '2 arguments exptected.', usage='(update! <map-1> <map-2>)' )

   try:
      map1._dict.update( map2._dict )
      return map1
   except:
      _lRuntimeError( 'update!', 'Invalid argument.' )
   
@LDefPrimitive( 'hasKey?' )        # (hasKey? <map> <key>)
def LP_hasKey( env, *args, **keys ):
   try:
      aMap,aKey = args
   except:
      _lRuntimeError( 'hasKey?', '2 arguments expected.', usage='(hasKey? <map> <key>)' )

   if isinstance( aKey, LSymbol ):
      aKey = aKey._val
   
   try:
      return 1 if aKey in aMap._dict else LNULL
   except:
      _lRuntimeError( 'hasKey?', 'Invalid argument.' )

# =====================
# Arithmetic Operations
# ---------------------
@LDefPrimitive( '+' )              # (+ <val1> <val2>)
def LP_add( env, *args, **keys ):
   if len(args) < 1:
      _lRuntimeError( '+', '1 or more arguments expected.', usage='(+ <number-1> <number-2> ...)' )

   try:
      return sum(iter(args))
   except:
      _lRuntimeError( '+', 'Invalid argument.' )

@LDefPrimitive( '-' )              # (- <val1> <val2>)
def LP_sub( env, *args, **keys ):
   argct = len(args)
   if len(args) < 1:
      _lRuntimeError( '-', '1 or more arguments expected.', usage='(- <number-1> <number-2> ...)' )

   try:
      if argct == 1:
         return -1 * args[0]
      else:
         return functools.reduce( lambda x,y: x - y, iter(args) )
   except:
      _lRuntimeError( '-', 'Invalid argument.' )

@LDefPrimitive( '*' )              # (* <val1> <val2>)
def LP_mul( env, *args, **keys ):
   if len(args) < 2:
      _lRuntimeError( '*', '2 or more arguments exptected.', usage='(* <number-1> <number-2> ...)' )

   try:
      return functools.reduce( lambda x,y: x * y, iter(args) )
   except:
      _lRuntimeError( '*', 'Invalid argument.' )

@LDefPrimitive( '/' )              # (/ <val1> <val2>)
def LP_div( env, *args, **keys ):
   if len(args) < 2:
      _lRuntimeError( '/', '2 or more arguments exptected.', usage='(/ <number-1> <number-2> ...)' )

   try:
      return functools.reduce( lambda x,y: x / y, iter(args) )
   except:
      _lRuntimeError( '/', 'Invalid argument.' )

@LDefPrimitive( '//' )             # (// <val1> <val2>)
def LP_intdiv( env, *args, **keys ):
   if len(args) != 2:
      _lRuntimeError( '//', '2 arguments expected.', usage='(// <number-1> <number-2>)' )

   try:
      return args[0] // args[1]
   except:
      _lRuntimeError( '//', 'Invalid argument.' )

@LDefPrimitive( 'mod' )            # (mod <val1> <val2>)
def LP_moddiv( env, *args, **keys ):
   if len(args) != 2:
      _lRuntimeError( 'mod', '2 arguments expected.', usage='(mod <number-1> <number-2>)' )

   try:
      return args[0] % args[1]
   except:
      _lRuntimeError( '%', 'Invalid argument.' )

@LDefPrimitive( 'trunc' )          # (trunc <expr>)
def LP_trunc( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'trunc', '1 argument exptected.', usage='(trunc <number>)' )

   try:
      return int(*args)
   except:
      _lRuntimeError( 'trunc', 'Invalid argument.' )

@LDefPrimitive( 'abs' )            # (abs <val>)
def LP_abs( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'abs', '1 argument exptected.', usage='(abs <number>)' )

   try:
      return abs(*args)
   except:
      _lRuntimeError( 'abs', 'Invalid argument.' )

@LDefPrimitive( 'log' )            # (log <x> [<base>])                         ;; if base if not provided, 10 is used.
def LP_log( env, *args, **keys ):
   numArgs = len(args)
   if not( 1 <= numArgs <= 2 ):
      _lRuntimeError( 'log', '1 or 2 arguments exptected.', usage='(log <x:number> [<base:number>])    ; base defaults to 10' )
   
   try:
      num,*rest = args
      base = 10 if len(rest) == 0 else rest[0]
      return math.log(num,base)
   except:
      _lRuntimeError( 'log', 'Invalid argument.' )

@LDefPrimitive( 'pow' )            # (pow <base> <power>)
def LP_pow( env, *args, **keys ):
   if len(args) != 2:
      _lRuntimeError( 'pow', '2 arguments expected.', usage='(pow <base:number> <power:number>)' )
   
   try:
      base,power = args
      return base ** power
   except:
      _lRuntimeError( 'pow', 'Invalid argument.' )

@LDefPrimitive( 'sin' )            # (sin <radians>)
def LP_sin( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'sin', '1 argument expected.', usage='(sin <radians:number>)' )

   try:
      return math.sin(*args)
   except:
      _lRuntimeError( 'sin', 'Invalid argument.' )

@LDefPrimitive( 'cos' )            # (cos <radians>)
def LP_cos( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'cos', '1 argument expected.', usage='(cos <radians:number>)' )

   try:
      return math.cos(*args)
   except:
      _lRuntimeError( 'cos', 'Invalid argument.' )

@LDefPrimitive( 'tan', '<radians:number>' ) # (tan <radians>)
def LP_tan( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError2( LP_tan, '1 argument expected.' )
   
   try:
      return math.tan(*args)
   except:
      _lRuntimeError( 'tan', 'Invalid argument.' )
   
@LDefPrimitive( 'exp', '<power:number>' )    # (exp <pow:number>)
def LP_exp( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError2( LP_exp, '1 argument expected.' )
   
   try:
      return math.exp(*args)
   except:
      _lRuntimeError2( LP_exp, 'Invalid Argument.' )

@LDefPrimitive( 'min' )            # (min <val1> <val2> ...)
def LP_min( env, *args, **Keys ):
   if len(args) < 1:
      _lRuntimeError( 'min', '1 or more arguments exptected.', usage='(min <number-1> <number-2> ...)' )
   
   try:
      return min( *args )
   except:
      _lRuntimeError( 'min', 'Invalid argument.' )

@LDefPrimitive( 'max' )            # (max <val1> <val2> ...)
def LP_max( env, *args, **keys ):
   if len(args) < 1:
      _lRuntimeError( 'max', '1 or more arguments exptected.', usage='(max <number-1> <number-2> ...)' )
   
   try:
      return max( *args )
   except:
      _lRuntimeError( 'max', 'Invalid argument.' )

# ==========
# Predicates
# ----------
@LDefPrimitive( 'isNull?' )        # (isNull? <expr>)
def LP_isNull( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'isNull?', '1 argument expected.', usage='(isNull? <expr>)' )

   arg1 = args[0]
   return 1 if (isinstance(arg1,LList) and (len(arg1) == 0)) else LNULL

@LDefPrimitive( 'isNumber?' )      # (isNumber?  <expr>)
def LP_isNumber( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'isNumber?', '1 argument expected.', usage='(isNumber? <expr>)' )

   return 1 if isinstance( args[0], L_NUMBER ) else LNULL

@LDefPrimitive( 'isSymbol?' )      # (isSymbol?  <expr>)
def LP_isSym( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'isSymbol?', '1 argument expected.', usage='(isSymbol? <expr>)' )

   return 1 if isinstance( args[0], LSymbol ) else LNULL

@LDefPrimitive( 'isAtom?' )        # (isAtom? <expr>) -> 1 if expr in { int, float, symbol }
def LP_isAtom( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'isAtom?', '1 argument expected.', usage='(isAtom? <expr>)' )

   return 1 if isinstance( args[0], L_ATOM ) else LNULL

@LDefPrimitive( 'isList?' )        # (isList? <expr>)
def LP_isList( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'isList?', '1 argument expected.', usage='(isList? <expr>)' )

   return 1 if isinstance( args[0], LList ) else LNULL

@LDefPrimitive( 'isMap?' )         # (isMap?  <expr>)
def LP_isMap( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'isMap?', '1 argument expected.', usage='(isMap? <expr>)' )

   return 1 if isinstance( args[0], LMap ) else LNULL

@LDefPrimitive( 'isString?' )      # (isString?  <expr>)
def LP_isStr( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'isString?', '1 argument expected.', usage='(isString? <expr>)' )

   return 1 if isinstance( args[0], str ) else LNULL

@LDefPrimitive( 'isFunction?' )    # (isFunction? <expr>)
def LP_isCall( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'isFunction?', '1 argument expected.', usage='(isFunction? <expr>)' )

   return 1 if isinstance( args[0], (LPrimitive,LFunction) ) else LNULL

# ====================
# Relational Operators
# --------------------
@LDefPrimitive( 'is?' )            # (is? <val1> <val2>)
def LP_is( env, *args, **keys ):
   try:
      arg1,arg2 = args
   except:
      _lRuntimeError( 'is?', '2 arguments exptected.', usage='(is? <object-1> <object-2>)' )
   
   if isinstance(arg1, (int,float,str)):
      return 1 if (arg1 == arg2) else LNULL
   else:
      return 1 if (arg1 is arg2) else LNULL

@LDefPrimitive( '=' )              # (=   <val1> <val2> ...)
def LP_equal( env, *args, **keys ):
   numArgs = len(args)
   if numArgs < 2:
      _lRuntimeError( '=', '2 or more arguments expected.', usage='(= <expr1> <expr2> ...)' )
   
   pairs = [ ]
   prior = None
   for mbr in args:
      if prior:
         pairs.append( (prior,mbr) )
      prior = mbr
   
   try:
      for arg1,arg2 in pairs:
         if not( arg1 == arg2 ):
            return LNULL
      
      return 1
   except:
      _lRuntimeError( '=', 'Unknown error.', usage='(= <expr1> <expr2> ...)' )

@LDefPrimitive( '<>' )             # (<>  <val1> <val2> ...)
def LP_notEqual( env, *args, **keys ):
   numArgs = len(args)
   if numArgs < 2:
      _lRuntimeError( '<>', '2 or more arguments expected.', usage='(<> <expr1> <expr2> ...)' )
   
   pairs = [ ]
   prior = None
   for mbr in args:
      if prior:
         pairs.append( (prior,mbr) )
      prior = mbr
   
   try:
      for arg1,arg2 in pairs:
         if not( arg1 != arg2 ):
            return LNULL
      
      return 1
   except:
      _lRuntimeError( '<>', 'Unknown error.', usage='(<> <expr1> <expr2> ...)' )

@LDefPrimitive( '<' )              # (<   <val1> <val2> ...)
def LP_less( env, *args, **keys ):
   numArgs = len(args)
   if numArgs < 2:
      _lRuntimeError( '<', '2 or more arguments expected.', usage='(< <expr1> <expr2> ...)' )
   
   pairs = [ ]
   prior = None
   for mbr in args:
      if prior:
         pairs.append( (prior,mbr) )
      prior = mbr
   
   try:
      for arg1,arg2 in pairs:
         if not( arg1 < arg2 ):
            return LNULL
      
      return 1
   except:
      _lRuntimeError( '<', 'Unknown error.', usage='(< <expr1> <expr2> ...)' )

@LDefPrimitive( '<=' )             # (<=  <val1> <val2> ...)
def LP_lessOrEqual( env, *args, **keys ):
   numArgs = len(args)
   if numArgs < 2:
      _lRuntimeError( '<=', '2 or more arguments expected.', usage='(<= <expr1> <expr2> ...)' )
   
   pairs = [ ]
   prior = None
   for mbr in args:
      if prior:
         pairs.append( (prior,mbr) )
      prior = mbr
   
   try:
      for arg1,arg2 in pairs:
         if not( arg1 <= arg2 ):
            return LNULL
      
      return 1
   except:
      _lRuntimeError( '<=', 'Unknown error.', usage='(<= <expr1> <expr2> ...)' )

@LDefPrimitive( '>' )              # (>   <val1> <val2> ...)
def LP_greater( env, *args, **keys ):
   numArgs = len(args)
   if numArgs < 2:
      _lRuntimeError( '>', '2 or more arguments expected.', usage='(> <expr1> <expr2> ...)' )
   
   pairs = [ ]
   prior = None
   for mbr in args:
      if prior:
         pairs.append( (prior,mbr) )
      prior = mbr
   
   try:
      for arg1,arg2 in pairs:
         if not( arg1 > arg2 ):
            return LNULL
      
      return 1
   except:
      _lRuntimeError( '>', 'Unknown error.', usage='(> <expr1> <expr2> ...)' )

@LDefPrimitive( '>=' )             # (>=  <val1> <val2> ...)
def LP_greaterOrEqual( env, *args, **keys ):
   numArgs = len(args)
   if numArgs < 2:
      _lRuntimeError( '>=', '2 or more arguments expected.', usage='(>= <expr1> <expr2> ...)' )
   
   pairs = [ ]
   prior = None
   for mbr in args:
      if prior:
         pairs.append( (prior,mbr) )
      prior = mbr
   
   try:
      for arg1,arg2 in pairs:
         if not( arg1 >= arg2 ):
            return LNULL
      
      return 1
   except:
      _lRuntimeError( '>=', 'Unknown error.', usage='(>= <expr1> <expr2> ...)' )

# =================
# Logical Operators
# -----------------
@LDefPrimitive( 'not' )            # (not <val>)
def LP_not( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'not', '1 argument exptected.', usage='(not <expr>)' )

   arg1 = args[0]
   return 1 if ((arg1 == 0) or (isinstance(arg1,LList) and len(arg1._list)==0) or (arg1 is None)) else LNULL

@LDefPrimitive( 'and' )            # (and <val1> <val2> ...)
def LP_and( env, *args, **keys ):
   if len(args) < 2:
      _lRuntimeError( 'and', '2 or more arguments exptected.', usage='(and <expr-1> <expr-2> ...)' )

   for arg in args:
      if (arg == 0) or (arg is LNULL) or (arg is None):
         return LNULL
   
   return 1

@LDefPrimitive( 'or' )             # (or  <val1> <val2> ...)
def LP_or( env, *args, **keys ):
   if len(args) < 2:
      _lRuntimeError( 'or', '2 or more arguments exptected.', usage='(or <expr-1> <expr-2> ...)' )

   for arg in args:
      if (arg != 0) and (arg is not LNULL) and (arg is not None):
         return 1
   
   return LNULL

# ===================
# String Manipulation
# -------------------
@LDefPrimitive( 'format' )         # (format <format String> '(<arg0> <arg1> ...))
def LP_format( env, *args, **keys ):
   try:
      formatString,formatArgs = args
   except:
      _lRuntimeError( 'format', '2 arguments exptected.', usage='(format <format:string> \'(<expr-1> <expr-2> ...) )' )

   try:
      return formatString.format( *(formatArgs._list) )
   except:
      _lRuntimeError( 'format', 'Unknown error.' )

# ===============
# Type Conversion
# ---------------
@LDefPrimitive( 'float' )          # (float <val>)
def LP_float( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'float', 'Exactly 1 argument expected.', usage='(float <number>)' )
   
   try:
      return float(args[0])
   except:
      _lRuntimeError( '+', 'Invalid argument.' )

@LDefPrimitive( 'string' )         # (string <expr1> <expr2> ...)   ; returns the concatenation of the string results of the arguments
def LP_string( env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'string', '1 argument exptected.', usage='(string <expr1> <expr2> ...)' )
   
   expr = args[0]
   
   try:
      if isinstance( expr, str ):
         return '"' + expr + '"'
      else:
         return str( expr )
   except:
      _lRuntimeError( 'string', 'Unknown error.', usage='(string <expr1> <expr2> ...)' )

# ===============
# I/O
# ---------------
@LDefPrimitive( 'write!' )         # (write! [<stream>] <string>)
def LP_write( env, *args, **keys ):
   numArgs = len(args)
   if not( 1 <= numArgs <= 2):
      _lRuntimeError( 'write!', '2 arguments expected', usage='(write! [<stream>] <string>)' )
   
   try:
      if numArgs == 1:
         stream = 'out'
         value  = args[0]
      else:
         stream,value = args
      
      if stream == 'out':
         print( value, sep='', end='', file=L_STDOUT )
      else:
         print( value, sep='', end='', file=stream )
      
      return value
   except:
      _lRuntimeError( 'write!', 'Unknown error.', usage='(write! [<stream>] <string>)' )

@LDefPrimitive( 'writeLn!' )       # (writeLn! [<stream>] <string>)
def LP_writeln( env, *args, **keys ):
   numArgs = len(args)
   if not( 1 <= numArgs <= 2):
      _lRuntimeError( 'write!', '2 arguments expected', usage='(write! [<stream>] <string>)' )
   
   try:
      if numArgs == 1:
         stream = 'out'
         value  = args[0]
      else:
         stream,value = args
      
      if stream == 'out':
         print( value, sep='', end='\n', file=L_STDOUT )
      else:
         print( value, sep='', end='\n', file=stream )
      
      return value
   except:
      _lRuntimeError( 'write!', 'Unknown error.', usage='(write! [<stream>] <string>)' )

@LDefPrimitive( 'read!' )          # (read! [<stream>] <readUpTo>)
def LP_read( env, *args, **keys ):
   numArgs = len(args)
   if numArgs > 2:
      _lRuntimeError( 'read!', '1 or 2 arguments expected.', usage='(read! [<stream>] <readUpTo>)' )
   
   try:
      if numArgs == 1:
         stream             = 'in'
         terminateCondition = args[0]
      else:
         stream,terminateCondition = args
      
      # unfinished
   except:
      pass

@LDefPrimitive( 'readLn!' )        # (readLn! [<stream>])
def LP_readLn( env, *args, **keys ):
   numArgs = len(args)
   if numArgs > 1:
      _lRuntimeError( 'read!', '0 or 1 arguments expected.', usage='(read! [<stream>])' )
   
   try:
      if numArgs == 0:
         stream = 'in'
      else:
         stream = args
      
      if stream == 'in':
         return input()
      else:
         return stream.read( )
   
   except:
      pass

# ===============
# Multi-Threading
# ---------------
@LDefPrimitive( 'parallel-eval' )  # (parallel-eval '(sharedVar1 sharedVar2 ...) '(expr1 expr2 expr3 ...))                    
def LP_parallel_eval( env, *args, **keys ):
   pass

@LDefPrimitive( 'wait!' )          # (wait! semaphoreName)
def LP_Wait( env, *args, **keys ):
   pass

@LDefPrimitive( 'signal! ' )       # (signal! semaphoreName)
def LP_Signal( env, *args, **keys ):
   pass

# ===============
# Misc
# ---------------
@LDefPrimitive( 'when' )           # (when)                      ; return the current date time as a list: (yr mn dy hr mn sec microsec)
def LP_when( env, *args, **keys ):
   if len(args) != 0:
      _lRuntimeError( 'when', '0 arguments exptected.', usage='(when)' )

   try:
      dt = datetime.datetime.now( )
      isinstance( dt, datetime.datetime )
      dateTuple = ( dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond )
      return LList( *dateTuple )
   except:
      _lRuntimeError( 'when', 'Unknown error.' )

@LDefPrimitive( 'symtab!' )        # (symtab!)
def LP_symtab( env, *args, **keys ):
   print( 'Symbol Table Dump:  Inner-Most Scope First')
   print( '------------------------------------------')
   try:
      while env:
         asLypsList = LList( *env.localSymbols() )
         print( str(asLypsList) )
         env = env.parentEnv()
   except:
      pass

# ===============
# E-Mind
# ---------------
@LDefPrimitive( 'primaries' )
def eM_primaries( env, *args, **keys ):             # (primaries '<expr>)
   if len(args) != 1:
      _lRuntimeError( 'primaries', '1 argument exptected.', usage='(primaries <form>)' )
   
   try:
      result = eM_primaries_aux( env, *args, **keys )
      return LList( *result )
   except:
      _lRuntimeError( 'primaries', 'Unknown error.' )

def eM_primaries_aux( env, *args, **keys ):
   # returns a python list of the primary (first) element in level of anExpr.
   # e.g. (and (not P) (implies X Y))  results in  (and not implies)
   anExpr = args[0]
   if not isinstance( anExpr, LList ):
      return [ ]
   elif len(anExpr._list) == 0:
      return [ ]
   else:
      # add the current level primary to the result list
      first = anExpr[0]
      result = [ first ]
   
      # recurse over each subordinate
      for subExpr in anExpr[1:]:
         result = result + eM_primaries_aux( env, subExpr )
   
      return result
   
@LDefPrimitive( 'OrderForms' )                      # (orderForms '(<form1> <form2> ...))
def eM_orderForms(  env, *args, **keys ):
   if len(args) != 1:
      _lRuntimeError( 'orderForms', '1 argument exptected.', usage='(orderForms \'(<form-1> <form-2> ...))' )
   
   formSet = args[0]
   
   try:
      # Create a dictionary: PrimariesStr    -> list of Form
      # Create a dictionary: PrimariesStrLen -> list of PrimariesStr
      primariesStrToFormsBin           = { }  # Map:  PrimariesStr    -> list of Form
      primariesLstLenToPrimariesStrBin = { }  # Map:  PrimariesLstLen -> list of PrimariesStr
      longestPrimariesLst = 0
      for form in formSet:
         # For the Form create PrimariesList and PrimariesStr
         primariesLst = eM_primaries( env, form )
      
         lst = [ str(elt._val) for elt in primariesLst ]
         primariesStr = ' '.join( lst )

         # Bin the form according to its PrimariesStr
         if primariesStr in primariesStrToFormsBin:
            primariesStrToFormsBin[ primariesStr ].append( form )
         else:
            primariesStrToFormsBin[ primariesStr ] = [ form ]
      
         # Bin the PrimariesStr according to its length
         primariesLstLen = len(primariesLst)
         longestPrimariesLst = max( primariesLstLen, longestPrimariesLst )
      
         if primariesLstLen in primariesLstLenToPrimariesStrBin:
            primariesLstLenToPrimariesStrBin[ primariesLstLen ].append( primariesStr )
         else:
            primariesLstLenToPrimariesStrBin[ primariesLstLen ] = [ primariesStr ]

      # Construct a new set ordered by binSize (shortest to longest)
      reorderedForms = [ ]
      extendReorderedForms = reorderedForms.extend
      for primariesLstLen in range( longestPrimariesLst, -1, -1 ):
         if primariesLstLen in primariesLstLenToPrimariesStrBin:
            primariesStrLst = primariesLstLenToPrimariesStrBin[ primariesLstLen ]
            for primariesStr in sorted( primariesStrLst, key=lambda pStr:len(primariesStrToFormsBin[pStr])):
               extendReorderedForms( primariesStrToFormsBin[primariesStr] )
   
      return LList(*reorderedForms)
   except:
      _lRuntimeError( 'orderForms', 'Unknown error.' )

@LDefPrimitive( 'mapForm', '<form> <instance:form> [<map>]' )
def eM_mapForm( env, *args, **keys ):
   if len(args) not in (2,3):
      _lRuntimeError2( eM_mapForm, '2 or 3 arguments expected.' )
   
   if len(args) == 3:
      form, expr, mapping = args
   else:
      form, expr = args
      mapping    = LMap( )
   
   try:
      return eM_mapForm_aux( env, form, expr, mapping )
   except:
      return LNULL

def eM_mapForm_aux( env, form, expr, mapping ):
   if isinstance( form, LSymbol ):
      try:
         formVal = mapping[form._val]
      except:
         mapping[ form._val ] = expr
         return mapping
      
      if _lTrue(_lEval3( env, 'EQUAL?', formVal, expr )):
         return mapping
      else:
         raise Exception()
   
   if isinstance(form,LList):
      if not isinstance(expr,LList):
         raise Exception()
      
      if len(expr) != len(form):
         raise Exception()
      
      if (not isinstance(expr[0],LSymbol)) or (not isinstance(form[0],LSymbol)):
         raise Exception 
      
      if expr[0] != form[0]:
         raise Exception()
      
      for subExpr, subForm in zip( expr.rest(), form.rest() ):
         eM_mapForm_aux( env, subForm, subExpr, mapping )
      
      return mapping

@LDefPrimitive( 'mapFormSet', '\'( <form1> <form2> ...) \'( <expr1> <expr2> ...)' )
def eM_mapFormSet( env, *args, **keys ):
   '''This method constructs a mapping from a set of forms to a set of exprs.
   Every form must map to some expr.  HOwever, some exprs may not be part of
   the mapping.
   mapFormSet returns a list of ( <map> <matches:list> ) where
   <map> is a set of symbols from the form set to <expr> in the expression.
   <matches:list> is a list of indecies into the set of expr such that the
   first index indicates which expr mapps to the first form, the second
   index is which expr mapps to the second form, etc.   Thus the list is the
   same length as the list of forms passed into mapFormSet.
   '''
   try:
      formList,exprList = args
   except:
      _lRuntimeError2( eM_mapFormSet, '2 arguments expected.' )
   
   try:
      # Let a formInfoList be [ form, primariesStr, candidateExpr1, candidateExpr2 ... ]
      # Here create a list of formInfoList
      # Where, candidateExpr is an index into exprList
      theFormInfoList = [ ]
      for form in formList:
         primLst = _lEval3( env, 'PRIMARIES', form )
         lst = [ str(elt._val) for elt in primLst ]
         theFormInfoList.append( [ form, ' '.join( lst ) ] )
   
      # Find expr candidates and append their indecies to the formInfoLists
      for exprId,expr in enumerate(exprList):
         primLst = _lEval3( env, 'PRIMARIES', expr )
         lst = [ str(elt._val) for elt in primLst ]
         exprPrimStr = ' '.join(lst)
      
         for formInfo in theFormInfoList:
            formPrimStr = formInfo[1]
            if exprPrimStr.startswith( formPrimStr ):
               formInfo.append( exprId )
   
      mapping = { }
      mapping,usedExprIndexList = eM_mapFormSet_aux( env, theFormInfoList, exprList, mapping, [ ] )
      return LList( LMap(**mapping), usedExprIndexList )
   except:
      return LNULL

def eM_mapFormSet_aux( env, formList, exprList, mapping, unavailableCandidates ):
   if len(formList) == 0:
      return mapping, unavailableCandidates
   else:
      form, formPrimStr, *candidateIDs = formList[0]
      
      for exprId in candidateIDs:
         if exprId in unavailableCandidates:
            continue
         
         expr = exprList[ exprId ]
         
         try:
            exprMap = _lEval3( env, 'MAPFORM', form, expr, mapping.copy() )
            if exprMap is LNULL:
               continue
            
            return eM_mapFormSet_aux(env, formList[1:], exprList, exprMap, unavailableCandidates + [ exprId ] )
         except:
            pass
      
      raise Exception( )

@LDefPrimitive( 'makeInstance', '<form> <map>' )
def eM_makeInstance( env, *args, **keys ):
   try:
      form,instMap = args
   except:
      _lRuntimeError2( 'makeInstance', '2 arguments expected.' )
   
   if isinstance( form, LSymbol ):
      try:
         return instMap[ form ]
      except:
         return form
   
   elif isinstance( form, LList ):
      resultLst = [ ]
      for subForm in form:
         resultLst.append( eM_makeInstance(env,subForm,instMap) )
      return LList( *resultLst )
   
   else:
      raise Exception( )

@LDefPrimitive( 'infer', '<conseq> <candidates:list>' )
def eM_infer( env, *args, **Keys ):
   try:
      conseqForm,candidateExprList = args
   except:
      _lRuntimeError2( eM_infer, '2 arguments expected.' )
   
   conseqSym,conseqInitialState,conseqFinalStates = conseqForm
   mapping = _lEval3( env, 'MAPFORMSET', conseqInitialState, candidateExprList )
   if mapping is not None:
      return _lEval3( env, 'MAKEINSTANCE', conseqFinalStates.first(), mapping )
   else:
      return LNULL

@LDefPrimitive( 'proofOpen', '<conclusion:form> <explicit givens>) \'(<assumption-1:form> <assumption-2:form> ...)' )
def eM_proofOpen( env, *args, **keys ):
   '''
   <explicit givens>
      list of <form>.  Assumptions or hypothesis to insert into the proof as
      the first lines.
   '''
   pass

@LDefPrimitive( 'proofClose', '<proof>' )
def eM_proofClose( env, *args, **keys ):
   pass

@LDefPrimitive( 'proofSteps', '<proof> [<closed:bool>|<stepNumbers:list>]' )
def eM_proofSteps( env, *args, **keys ):
   '''
   Return a pair of lists ( (<form-1> <form-2> ...) (<stepForm-1:int> <stepForm-2:int> ...) )
   Both lists are of the same length.
   The first is a list of forms from the proof whose steps are open/closed (determined by 2nd argument).
   The second is a list of proof step numbers corresponding to the forms in the first list.
   e.g.
         (
            ( 6         8                   )
            ( (AND P Q) (NOT (IMPLIES X Y)) )
         )
         
         Meaning that the first form is step 6 in the proof and the second form is step 8.
   
   <proof>
      The proof we are working with.
   
   <closed>
      If true only closed steps are returned.
      If false only open steps are returned.
      If omitted all steps are returned.
   
   <stepNumbers:list>
      If supplied (as an alternative to <closed>), the specified step numbers are returned.
   '''
   pass

@LDefPrimitive( 'proofChangeSteps', '<proof> <stepNumbers:list> [<close:bool>]' )
def eM_proofCloseSteps( env, *args, **keys ):
   '''
   Close the step numbers of the proof indicated in <stepNumbers:list>.
   
   <close>
      If true or omitted, the indicated step numbers are closed.
      If false the indicated step numbers are opened.
   '''
   pass

@LDefPrimitive( 'proofAccessibleSteps', '<proof> <stepNum>')
def eM_proofAccessible( env, *args, **keys ):
   '''
   returns a list of step numbers validly accessible from <stepNum>.
   '''
   pass

@LDefPrimitive( 'beginProof', '<conclusion:form> \'(<assumption-1:form> <assumption-2:form> ...)' )
def eM_beginProof( env, *args, **keys ):
   try:
      conclusionForm,assumptionList = args
   except:
      _lRuntimeError2( eM_beginProof, '2 arguments expected.' )
   
   proofSteps = [ ]
   for stepNum,assumption in enumerate(assumptionList):
      theStep = [ stepNum + 1, assumption, LList( 'Assumption', LList(), LMap() ) ]
      proofSteps.append( theStep )
   
   proofSteps = eM_prove( conclusionForm, assumptionList, proofSteps )
   theProof = [ LSymbol('PROOF'), conclusionForm, assumptionList, proofSteps ]
   
   return LList( *theProof )
   
@LDefPrimitive( 'prove', '<conclusion:form> <premiseList> <proofSoFar>' )
def eM_prove( env, *args, **keys ):
   try:
      conclusionForm,premiseList,proofSoFar = args
   except:
      _lRuntimeError2( eM_prove, '3 arguments expected.' )
   
   
   
   
'''
<Proof>:
   (proof <conclusion:form> (<assumption-1:form> <assumption-2:form> ...)
      ( ('var' a b c ...)
      (<closed:bool> 1 <world> <form> <reason>)
      (<closed:bool> 2 <world> <form> <reason>)
      (<closed:bool> 3
         (proof <conclusion:form> (<hypothesis:form>)
            ( ('var' a b c ...)
            (<closed:bool> 3 <world> <form> <reason>)
            (<closed:bool> 4 <world> <form> <reason>)
            ) ) )
      (<closed:bool> 5 <form> <reason>)
      )
   )

<reason>:
   ( <formName:symbol> <premise ref list> <map> )
   
'''

'''
@LDefPrimitive( 'defun!' )         # (defun!  '(<name> <args>) '<expr>) ;; def a function locally
ef LP_defunLocal( env, args ):    
   funcNameSym = args[0].first()
   funcParams  = args[0].rest()
   funcBody    = args[1]
   
   funcDef     = LFunction( funcNameSym._val, funcParams, funcBody )
   
   return env.defLocal( funcNameSym._val, funcDef )

@LDefPrimitive( 'defun!!' )        # (defun!! '(<name> <args>) '<expr>) ;; def a function globally
aef LP_defunGlobal( env, args ):   
   funcNameSym = args[0].first()
   funcParams  = args[0].rest()
   funcBody    = args[1]
   
   funcDef     = LFunction( funcNameSym._val, funcParams, funcBody )
   
   return env.defGlobal( funcNameSym._val, funcDef )
'''
