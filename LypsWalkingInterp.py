from LypsImpl import *
import sys

class LypsWalkingInterpreter( object ):
   def __init__( self ):
      self._codeSeg = None
      self._env     = LEnv( )
      self.reboot( )
   
   def reboot( self ):
      self._env = self._env.reInitialize( )
      return
   
   def interpret( self, ast, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr ):
      global L_STDIN, L_STDOUT, L_STDERR
      L_STDIN  = stdin
      L_STDOUT = stdout
      L_STDERR = stderr
      
      self._codeSeg = [ ]
      try:
         return self._interpret( self._env, ast )
      finally:
         L_STDIN  = sys.stdin
         L_STDOUT = sys.stdout
         L_STDERR = sys.stderr
   
   def _interpret( self, env, ast ):
      return self._lEval( env, ast )
   
   def _interpret_list( self, env, ast ):
      if len(ast._list) == 0:
         return LNULL
      
      # The Function name
      try:
         fnName   = ast[0]._val
         exprArgs = ast[1:]
      except:
         raise LypsRuntimeError( 'Badly formed list expression - function name expected.' )

      if fnName == 'QUOTE':
         return ast[1]
      
      # Evaluate each arg
      evaluatedArgs = [ ]
      evaluatedKeys = { }
      for argNum,argExpr in enumerate(exprArgs):
         try:
            evaluatedArg = self._lEval( env, argExpr )
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
         if isinstance( fnDef, LFunction ):
            return self._interpret_LFunction( fnDef, env, *evaluatedArgs, **evaluatedKeys )
         elif isinstance( fnDef, LPrimitive ):
            return fnDef._fn( env, *evaluatedArgs, **evaluatedKeys )
      except TypeError as ex:
         raise LypsRuntimeError( 'Error evaluating list expression {0}.'.format(fnName) )

   def _interpret_LFunction( self, aFnDef, env, *args, **keys ):
      env = env.openScope( )
      
      # store the arguments as locals
      for paramName, argVal in zip( aFnDef._params._list, args ):
         env.defLocal( paramName, argVal )
      
      body = aFnDef._body
      
      if isinstance(body, (int,float,str)):
         return body
      else:
         return self._lEval( env, body )

   def _interpret_LSymbol( self, env, ast ):
      try:
         return env.getValue( ast )
      except:
         return self

   def _lEval( self, env, expr ):
      '''
      Evaluate expr as a lyps expression.
      Note:  Symbols (including function names) need to be in capitals before
      invoking this function.
      '''
      if isinstance( expr, (L_ATOM,LMap) ):
         return expr
      elif isinstance( expr, LSymbol ):
         return self._interpret_LSymbol( env, expr )
      elif isinstance( expr, LList ):
         return self._interpret_list( env, expr )
      elif isinstance( expr, LFunction ):
         pass
      else:
         raise Exception( 'Unknown' )
         #return expr.eval( env )

   def _lEval2( self, env, *expr ):
      '''
      Evaluate expr as a lyps list expression.
      Note:  Symbols (including function names) need to be in capitals before
      invoking this function.
      '''
      expr = LList( *expr )
      return self._interpret_list( expr, env )
      #return expr.eval( env )

   def _lEval3( self, env, fnName, *args ):
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
      return self._interpret_list( env, theExprList )

   def _lTrue( self, expr ):
      return (expr is not LNULL) and (expr != 0)

   
   