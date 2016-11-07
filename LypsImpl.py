import math
import datetime
import fractions
import functools
import sys
from ltk_py3.Environment import Environment as LEnv

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

# Python / Lyps Type Representation Mapping
L_NUMBER = (int,float,fractions.Fraction)
L_ATOM   = (int,float,fractions.Fraction,str)

def evalLypsExpr( anEnv, parsedExpr, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr ):
   global L_STDIN, L_STDOUT, L_STDERR
   resultExpr = None
   if isinstance(parsedExpr, L_ATOM):
      resultExpr = parsedExpr
   else:
      try:
         L_STDIN  = stdin
         L_STDOUT = stdout
         L_STDERR = stderr
         
         resultExpr = parsedExpr.eval( anEnv )
      finally:
         L_STDIN  = sys.stdin
         L_STDOUT = sys.stdout
         L_STDERR = sys.stderr
   
   return resultExpr

def beautifyLypsExpr( lypsObj ):
   '''Return a printable, formatted python string representation
   of a lyps object.'''
   if isinstance( lypsObj, str ):
      return '"' + lypsObj + '"'
   else:
      return str( lypsObj )

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
L_STDERR = sys.stderr

# ##############################
# The Lyps Execution Environment
class __LEnv( object ):
   PRMITIVE_LIST = [ ]
   GLOBAL_SCOPE  = None

   def __init__( self, parent=None ):
      self._parent = parent
      self._locals = { }
      
      if LEnv.GLOBAL_SCOPE is None:
         LEnv.GLOBAL_SCOPE = self
         self.reInitialize( )

   def reInitialize( self, newValueDict=None ):
      root = LEnv.GLOBAL_SCOPE
      root._parent = None
      #root._locals = { name:value for name,value in LEnv.PRMITIVE_LIST }
      if newValueDict is None:
         root._locals = { name:value for name,value in LEnv.PRMITIVE_LIST }
      else:
         self._locals = newValueDict
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
   
   def isDefined( self, symStr ):
      if symStr in self._locals:
         return True
      elif self._parent is None:
         return False
      else:
         return self._parent.isBound( symStr )
   

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

'''
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
'''
