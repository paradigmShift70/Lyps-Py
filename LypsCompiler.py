from LypsImpl import *
from ltk_py3.Environment import Environment
from ltk_py3.stackvm1 import assemble, CodeObject1
import sys

LGlobalSymbol = { }

class LypsCompiler( object ):
   def __init__( self ):
      self._codeSeg = [ ]

   @staticmethod
   def defaultEnv( ):
      result = Environment( parent=None, primitives=LGlobalSymbol )
      return result

   def compile( self, symTab, ast ):
      self._codeSeg = [ ]
      self._compileObject( symTab, ast, self._codeSeg, lvalue=False )
      self._codeSeg.append( ( 'HALT', ) )
      return self._codeSeg
   
   def _compileObject( self, symTab, ast, codeSeg, lvalue=False ):
      if isinstance( ast, L_ATOM ):
         codeSeg.append( ( 'PUSH', ast ) )
      elif isinstance( ast, LSymbol ):
         if lvalue:
            codeSeg.append( ( 'PUSH', ast._val ) )
         else:
            codeSeg.append( ( 'PUSH', ast._sym ) )
            codeSeg.append( ( 'GET' )            )
      elif isinstance( ast, LList ):
         self._compileList( symTab, ast, codeSeg )
      elif isinstance( ast, LFunction ):
         return self._compileFunction( symTab, ast )
      else:
         raise Exception( 'Unknown' )

   def _compileList( self, symTab, ast, codeSeg ):
      if len(ast._list) == 0:
         codeSeg.append( (None, 'PUSH', LNULL) )
         return
      
      # The Function name
      try:
         fnName   = ast[0]._val
         exprArgs = ast[1:]
      except:
         raise LypsRuntimeError( 'Badly formed list expression - function name expected.' )

      # Evaluate each arg
      for argNum,argAST in enumerate(exprArgs):
         self._compileObject( symTab, argAST, codeSeg, lvalue=False )
      
      codeSeg.append( (   'PUSH',      len(exprArgs)) )
      codeSeg.append( (   'lPACK',                  ) )
      codeSeg.append( (   'lREVERSE',               ) )
      codeSeg.append( (   'lUNPACK',                ) )
      codeSeg.append( (   'POP',                    ) ) # top item from lUNPACK is the len of the list
      
      # Get the function definition
      codeSeg.append( ( 'PUSH',          fnName ) )
      codeSeg.append( ( 'DEREF',                ) )
      codeSeg.append( ( 'CALL',   len(exprArgs) ) )

class LypsCompiler_( object ):
   def __init__( self ):
      self._codeSeg = None
      self._env     = LEnv( )
      self.reboot( )
   
   def reboot( self ):
      global LGlobalSymbol
      self._env = self._env.reInitialize( LGlobalSymbol )
      return
   
   def compile( self, ast ):
      codeSeg = [ ]
      self._compile( codeSeg, self._env, ast )
   
   def _compile( self, codeSeg, env, ast ):
      self.compileObject( codeSeg, env, ast )
   
   def _compile_list( self, codeSeg, env, ast ):
      if len(ast._list) == 0:
         codeSeg.append( (None, 'PUSH', LNULL) )
         return
      
      # The Function name
      try:
         fnName   = ast[0]._val
         exprArgs = ast[1:]
      except:
         raise LypsRuntimeError( 'Badly formed list expression - function name expected.' )

      # Evaluate each arg
      for argNum,argExpr in enumerate(exprArgs):
         self.compileObject( codeSeg, env, argExpr ) # result is on stack
      
      codeSeg.append( (None,   'lPACK',     len(exprArgs)) )
      codeSeg.append( (None,   'lREVERSE'                ) )
      codeSeg.append( (None,   'lUNPACK'                 ) )
      
      # Get the function definition
      if env.isBound(fnName):
         codeSeg.append( (None, 'PUSH',     fnName) )
         codeSeg.append( (None, 'GET',            ) )
      else:
         raise LypsRuntimeError( 'Symbol {0} is not the name of a function.'.format(fnName) )

      # Evaluate the top level function
      if isinstance( fnDef, LFunction ):
         self._compile_LFunction( codeSeg, env )  # Function def is at the top of stack
         return
      elif isinstance( fnDef, LPrimitive ):
         fnDef._fn( codeSeg, env )  # Primitive def is at the top of stack
         return

   def _compile_LFunction( self, codeSeg, env ):
      # fnDef is at the top of stack, args are just below it
      env = env.openScope( )
      
      # store the arguments as locals
      for paramName, argVal in zip( aFnDef._params._list, args ):
         env.defLocal( paramName, argVal )
      
      body = aFnDef._body
      
      if isinstance(body, (int,float,str)):
         codeSeg.append( (None,     'PUSH',    body) )
         return
      else:
         self.compileObject( codeSeg, env, body )
         return

   def _compile_LSymbol( self, codeSeg, env, ast ):
      if env.isBound( ast ):
         codeTemplate = [
            (             'PUSH',        ast ),
            (             'GET'              ),
            ]
      else:
         codeTemplate = [
            (             'PUSH',        ast )
            ]
      
      codeSeg.extend( codeTemplate )

   def compileObject( self, codeSeg, env, ast ):
      '''
      Evaluate ast as a lyps expression.
      Note:  Symbols (including function names) need to be in capitals before
      invoking this function.
      
      returns compiled object
      '''
      if isinstance( ast, (L_ATOM,LMap) ):
         codeSeg.append( ast )
      elif isinstance( ast, LSymbol ):
         self._compile_LSymbol( codeSeg, env, ast )
      elif isinstance( ast, LList ):
         self._compile_list( codeSeg, env, ast )
      elif isinstance( ast, LFunction ):
         pass
      else:
         raise Exception( 'Unknown' )
         #return ast.eval( env )



if True:
   LNULL = LList()
   LGlobalSymbol[ 'NULL' ] = LNULL
   LGlobalSymbol[ 'PI'   ] = math.pi
   LGlobalSymbol[ 'E'    ] = math.e
   LGlobalSymbol[ 'INF'  ] = math.inf
   LGlobalSymbol[ '-INF' ] = -math.inf
   LGlobalSymbol[ '-NAN' ] = math.nan

   def CodeSeg( *instructions ):
      res = assemble( instructions )
      return res

   LGlobalSymbol[ 'DEF!'  ] =  CodeSeg(
      (             'PUSH_BPOFF',   -2 ),   # PUSH object
      (             'PUSH_BPOFF',   -1 ),   # PUSH symbol   # [ ..., object, symbol ]
      (             'DEF',             ),
      (             'RET',             )
      )

   LGlobalSymbol[ 'DEF!!'  ] =  CodeSeg(
      (             'PUSH_BPOFF',   -2 ),   # PUSH object
      (             'PUSH_BPOFF',   -1 ),   # PUSH symbol   # [ ..., object, symbol ]
      (             'DEFG',            ),
      (             'RET',             )
      )

   LGlobalSymbol[ 'SET!'   ] =  CodeSeg(
      (             'PUSH_BPOFF',   -2 ),   # PUSH object
      (             'PUSH_BPOFF',   -1 ),   # PUSH symbol   # [ ..., object, symbol ]
      (             'SET',             ),
      (             'RET',             )
      )

   LGlobalSymbol[ 'UNDEF!'   ] =  CodeSeg(
      (             'PUSH_BPOFF',   -1 ),   # PUSH symbol   # [ ..., object, symbol ]
      (             'UNDEF',           ),
      (             'RET',             )
      )

   LGlobalSymbol[ '+'        ] = CodeSeg(
      (              'PUSH_BPOFF',     -1 ),
      (              'PUSH_BPOFF',     -2 ),
      (              'iADD',              ),
      (              'RET',               )
      )
   
   LGlobalSymbol[ '-'        ] = CodeSeg(
      (              'PUSH_BPOFF',     -1 ),
      (              'PUSH_BPOFF',     -2 ),
      (              'iSUB',              ),
      (              'RET',               )
      )
   
   LGlobalSymbol[ 'FIB'      ] = CodeSeg(
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH',                  2 ],
      [                  'iGT'                      ],
      [                  'JMP_T',           'else:' ],
      [                  'PUSH',                  1 ],
      [                  'RET'                      ],
      [ 'else:',         'PUSH_BPOFF',           -1 ],
      [                  'iDEC'                     ],
      [                  'PUSH_CS'                  ],
      [                  'CALL',                  1 ], # Recursive call
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH',                  2 ],
      [                  'iSUB'                     ],
      [                  'PUSH_CS'                  ],
      [                  'CALL',                  1 ],   # Recursive call
      [                  'iADD'                     ],
      [ 'end:',          'RET'                      ]
      )

   # =================
   # Symbol Definition
   # -----------------

   def CodeSeg( *args, **keys ):
      return assemble( *args )

   def DefineFn( argNameList, *body ):
      return body
   
if False:
   class LDefPrimitive( object ):
      def __init__( self, primitiveSymbol, args=None ):
         self._name  = primitiveSymbol.upper( )
         if args is not None:
            self._usage = '({0} {1})'.format( primitiveSymbol, args )
         else:
            self._usage = None
   
      #def __call__( self, primitiveDef ):
         #lPrimitivObj = LPrimitive( primitiveDef )
         #lPrimitivObj.__lname__    = self._name
         #lPrimitivObj.__lusage__   = self._usage
         #LGlobalSymbol[self._name] = lPrimitivObj
         #return lPrimitivObj

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

      LGlobalSymbol[ 'LAM' ] = CodeSeg(
      # arg -1 is a list of paramNames
      # arg -2 is a function body
   
      # 1. Construct prefix code to precede function body
      #    BEGIN
   
      # 2. forEach paramNum, paramName in stackTop:
      #    PUSH -1 - paramNum
      #    PUSH paramNum
      #    DEF
   
      # 3. Construct suffix code to follow function body
   
      # 4. Construct a single list as the concatenation of:
      #       - the prefix code
      #       - the body
      #       - the suffix code
      )

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
         return LNULL #LList()
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
   
