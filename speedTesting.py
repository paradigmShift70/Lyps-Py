
#!python3.5

import itertools
import operator as op
import math
import copy

try:
   from Environment import Environment
except:
   from ltk_py3.Environment import Environment

class INTERRUPT( Exception ):
   def __init__( self, name ):
      super().__init__( )
      self.name = name

# Flags
NO_ERROR              = 0
CARRY                 = 1
STACK_OF              = 2
STACK_UF              = 3
UNKNOWN_UNRECOVERABLE = 4
BAD_ADDRESS           = 8
HALT                  = 9
   
# Registers
CS      = None  # The Code Segment
CP      = 0     # The Code Pointer
IR      = ''    # Instruction Register
      
SS      = [ ]   # The Stack Segment
SP      = 0     # The Stack Pointer (running value for len(_SS))
      
BP      = 0     # Base Pointer
BINF    = None  # Base Info
      
FLG     = 0     # Flag Register
CT      = 0     # Instruction Counter
   
ENV     = Environment( )
last    = None  # Most recent result
      
OPS     = { }       # Map:  opname -> opFn
DOC     = { }
CAT     = { }

# Initialize
for name in dir(StackVM1):
   if name.startswith( 'op_' ):
      fn              = getattr( __file__ , name )
      OPS[ name[3:] ] = fn
      try:
         docs = parseDoc( fn.__doc__ )
         DOC[ name[3:] ] = docs
         cat = docs[-1]
      except:
         DOC[ name[3:] ] = (name[3:],'- UNDOCUMENTED -',('',''),'','')
         cat = ''
            
      if cat not in CAT:
         CAT[ cat ] = [ name[3:] ]
      else:
         CAT[ cat ].append( name[3:] )
      
for cat in CAT.keys():
   CAT[cat] = sorted(CAT[cat])
   
  
def _run_( ):
   '''Set CS,CP,ENV prior to calling run.'''
   ENV = env
   FLG = 0
   
   while True:
      while FLG == 0:
         fetch()
         decode()
         execute()

   if FLG == HALT:
      return stack[-1]
   else:
      pass

def run( ):
   '''Set CS,CP,ENV prior to calling run.'''
   CP = 0
   FLG = 0
   
   while True:
      try:
         while True:
            OP[CS[CP]]( )
            #self.IR = self.CS[ self.CP ]
            #self.IR( )
      except INTERRUPT as IRQ:
         if IRQ.name == 'HALT':
            last = SS[-1]
            return last
         else:
            raise

def run_p( ):
   '''Set CS,CP,ENV prior to calling run.'''
   CP = 0
   FLG = 0
   
   while True:
      try:
         while True:
            CS[CP]( )
      except INTERRUPT as IRQ:
         if IRQ.name == 'HALT':
            last = SS[-1]
            return last
         else:
            raise

def iterrun( ):
   CP = 0
   FLG = StackVM.NO_ERROR
   
   while True:
      try:
         while True:
            yield self
            CS[CP]( )
      except INTERRUPT as IRQ:
         if IRQ.name == 'HALT':
            last = SS[-1]
            raise StopIteration()
         else:
            raise

# #######
# PROBES & OPCODE implementation tools
def _trace( instructionNum, hexintegers=False ):
   if hexintegers:
      print( '{:012X}:{:06X}:  {:22s} || {:s}'.format( instructionNum, CP, _trace_instruction(hexintegers=hexintegers), _trace_stack(40,hexintegers=hexintegers) ) )
   else:
      print( '{:012d}:{:06d}:  {:22s} || {:s}'.format( instructionNum, CP, _trace_instruction(), _trace_stack(40) ) )

def _trace_instruction( hexintegers=False ):
   opcode = CS[ CP ]
   
   # Disassemble the Current Instruction
   operandList = [ ]
   for operand in CS[CP + 1 : ]:
      if isinstance( operand, int ) and hexintegers:
         operandList.append( hex(operand).upper() )
      elif isinstance( operand, (int,float,bool) ):
         operandList.append( str(operand) )
      elif isinstance( operand, str ):
         if operand in OP:
            break
         else:
            operandList.append( operand[:12] )
      elif isinstance( operand, list ):
         operandList.append( '[...]' )
      elif isinstance( operand, tuple ):
         operandList.append( '(...)' )
      else:
         raise Exception( )
   
   operandListStr = ', '.join( operandList ).rstrip()
   result = '{0:10s}  {1:10}'.format(opcode,operandListStr)
   return result

def _trace_stack( fieldSize=50, hexintegers=False ):
   return str(SS)[-fieldSize:].rjust(fieldSize)

def doc_instructionSet( ):
   for cat in sorted(CAT.keys()):
      print( 'CATEGORY: {:s}'.format(cat) )
      print( '----------' + ('-' * len(cat)) )
      
      for opName in CAT[cat]:
         op,usage,stack,descr,cat = DOC[opName]
         print( 'Instruction:  {:s}'.format(usage))
         print( '      Stack:  {:s}  ->  {:s}'.format(*stack))
         print( '      Note:   {:s}'.format(descr))

def top( num ):
   return SS[ 0 - num : ]

def IDENTITY( arg ):
   return arg

def UNARY_OP( type1, fn ):
   #arg1 = SS[ -1 ]
   SS[ -1 ] = fn( type1(SS[-1]) )
   CP += 1

def BINARY_OP( fn, type1, type2 ):
   arg2 = SS.pop( )
   #arg1 = SS[ -1 ]
   SS[ -1 ] = fn( type1(SS[-1]), type2(arg2) )
   CP += 1

#def BINARY_OP( fn, type1, type2 ):
   # Weakly Typed Version
   #SS[-1] = (lambda x: SS[-1]   +   x)(SS.pop())
   #CP += 1
   
   # Strongly Typed Version
   #SS[-1] = (lambda x: type1(SS[-1])   +   type2(x))(SS.pop())
   #CP += 1

def BINARY_OP2( fn, type1, type2 ):
   #'''Same as above but swapps the args to fn()'''
   arg2 = SS.pop( )
   #arg1 = SS[ -1 ]
   SS[ -1 ] = fn( type1(arg2), type2(SS[-1]) )
   CP += 1

#def BINARY_OP2( fn, type1, type2 ):
   #SS[-1] = (lambda x: x   +   SS[-1])(SS.pop())
   #CP += 1

def JUMP_OP( ):
   CP = CS[ CP + 1 ]

def CJUMP_OP( fn ):
   arg1 = SS.pop( )
   if fn(arg1):
      CP = CS[ CP + 1 ]
   else:
      CP += 2

# #######
# OPCODES

# patterns
# - to get the top n items:
#     arg1, arg2 = _SS[ -2 : ]
# - to replace stack top (push without popping)
#     _[ -1 ] = val
# - to get an operand (which follows an opcode)
#  operand = self._CS[ _CP + 1 ]    # get operand

# Stack Operations
def op_PUSH( ):
   '''PUSH <value>
   SS:  [ ... ]  ->  [ ..., <value> ]
   :    Push a value onto the stack.
   #STACK
   '''
   SS.append( CS[ CP + 1 ] )  # get operand
   CP += 2

def op_POP( ):                      # POP <count>
   '''POP
   SS:  [ ..., <top> ]  ->  [ ... ]
   :    Remove and discard one item from the top of the stack.
   #STACK
   '''
   SS.pop( )
   CP += 1

def op_POPn( ):                     # POPn <count>
   '''POP <count>
   SS:  [ ... ]  ->  [ ... ]
   :    Remove and discard <count> items from the top of the stack
   #STACK
   '''
   operand = CS[ CP + 1 ]    # get operand
   result = SS[ 0 - operand : ]
   del SS[ 0 - operand : ]
   CP =+ 2

def op_TOPSET( ):                   # TOPSET <val>
   '''TOPSET <value>
   SS:  [ ..., <oldTop> ]  ->  [ ..., <value> ]
   :    Replace the stack's top item with <value>.
   #STACK
   '''
   operand = CS[ CP + 1 ]    # get operand
   SS[ -1 ] = val      
   CP += 2

def op_PUSH_NTH( ):
   '''PUSH_NTH <offset>
   SS:  [ ... ]  ->  [ ..., <nthItem>
   :    Push the nth (-1, -2, etc.) offset from the stack top.
   #STACK
   '''
   operand = CS[ CP + 1 ]    # get operand
   SS.append( SS[ 0 - operand ] )      
   CP += 2

def op_SWAPXY( ):
   '''SWAPXY
   SS:  [ ..., <x>, <y> ]  ->  [ ..., <y>, <x> ]
   :    Swap the two top stack items.
   #STACK
   '''
   SS[ 0 - 2 ], SS[ 0 - 1 ] = SS[ 0 - 2 : ]
   CP += 1

# Environment Management
def op_BIND( ):
   '''BIND
   SS:  [ ..., <value>, <symbol> ]  ->  [ ..., <value> ]
   :    Bind a symbold to a value in the local namespace.
   #ENVIRONMENT
   '''
   name = SS.pop( )
   obj  = SS[ -1 ]
   ENV.declLocal( name, obj )
   CP += 1

def op_BINDG( ):
   '''BINDG
   SS:  [ ..., <value>, <symbol> ]  ->  [ ..., <value> ]
   :    Bind a symbol to a value in the global namespace.
   #ENVIRONMENT
   '''
   name = SS.pop( )
   obj  = SS[ -1 ]
   ENV.declGlobal( name, obj )
   CP += 1

def op_UNBIND( ):
   '''UNBIND
   SS:  [ ..., <symbol> ]  ->  [ ... ]
   :    Remove any bindings to the symbol.
   #ENVIRONMENT
   '''
   name = SS.pop( )
   ENV.unDecl( name )
   sefl.CP += 1

def op_REBIND( ):
   '''BIND
   SS:  [ ..., <value>, <symbol> ]  ->  [ ..., <value> ]
   :    Rebind a symbol to a new value.
   #ENVIRONMENT
   '''
   name = SS.pop( )
   obj  = SS[ -1 ]
   ENV.rebind( name, obj )
   CP += 1

def op_DEREF( ):
   '''DEREF
   SS:  [ ..., <symbol> ]  ->  [ ..., <value> ]
   :    Get value to which a symbol is bound.
   :    If <symbol> is not bound, <value> will be <symbol>
   #ENVIRONMENT
   '''
   name = SS[-1]
   SS[-1] = ENV.get( name )
   CP += 1

def op_BEGIN( ):
   '''BEGIN
   :    Begin/Open a new nested lexical scope in the environment.
   #ENVIRONMENT
   '''
   ENV = Environment( ENV )
   CP += 1

def op_END( ):
   '''END
   :    End/Close the current nested lexical scope in the environment.
   #ENVIRONMENT
   '''
   ENV = ENV.parentEnv( )
   CP += 1

# Register Controls
def op_PUSH_CS( ):
   '''PUSH_CS
   SS:  [ ... ]  ->  [ ..., <saved CS> ]
   :    Push a copy of CS onto the stack.
   #REGISTERS
   '''
   SS.append( CS )
   CP += 1

def op_POP_CS( ):
   '''POP_CS
   SS:  [ ..., <saved CS> ]  ->  [ ... ]
   :    Pop the top of the stack, placing the popped value into CS.
   #REGISTERS
   '''
   CS = SS.pop( )
   CP += 1

def op_PUSH_FLG( ):
   '''PUSH_FLG
   SS:  [ ... ]  ->  [ ..., <saved FLG> ]
   :    Push a copy of FLG onto the stack.
   #REGISTERS
   '''
   SS.append( FLG )
   CP += 1

def op_POP_FLG( ):
   '''POP_FLG
   SS:  [ ..., <saved FLG> ]  ->  [ ... ]
   :    Pop the top of the stack, placing the popped value into FLG.
   #REGISTERS
   '''
   FLG = SS.pop( )
   CP += 1

# Subroutine
def op_CALL( ):
   '''CALL <argumentCount>
   SS:  [ ..., <argn>, ..., <arg2>, <arg1>, <newCodeSeg> ]  -> [ ..., <argn>, ..., <arg2>, <arg1> ]
   :    Call the <newCodeSeg>.
   #CALL
   '''
   # Prepare new Stack Frame & Return Info
   newCodeSeg = SS.pop( )
   numArgs    = CS[CP+1]
   
   # Save current stack frame
   SP    = len(SS)     # SP set to stack top
   
   ret_SP = SP - numArgs
   ret_BP = BP
   ret_CS = CS
   ret_CP = CP + 2
   
   BINF  = [ret_CS, ret_CP, ret_SP, ret_BP, BINF]
   
   # Construct new stack frame
   BP    = SP             # BP points to argument 0
   CS    = newCodeSeg
   CP    = 0

def op_CALLr( ):
   '''CALLr <argumentCount>
   SS:  [ ..., <argn>, ..., <arg2>, <arg1> ]  -> [ ..., <argn>, ..., <arg2>, <arg1> ]
   :    Call the current Code Segment (CS) recursively.
   :    Convenience.  Equivalent to:  Push_CS; CALL <argumentCount>;
   #CALL CONVENIENCE
   '''
   # Prepare new Stack Frame & Return Info
   newCodeSeg = CS
   numArgs    = CS[CP+1]
   
   # Save current stack frame
   SP    = len(SS)     # SP set to stack top
   
   ret_SP = SP - numArgs
   ret_BP = BP
   ret_CS = CS
   ret_CP = CP + 2
   
   BINF  = [ret_CS, ret_CP, ret_SP, ret_BP, BINF]
   
   # Construct new stack frame
   BP    = SP             # BP points to argument 0
   CS    = newCodeSeg
   CP    = 0

def op_RET( ):
   '''RET
   SS:  [ ..., <stack frame>, <return value> ]  ->  [ ..., <return value> ]
   :    Restore the prior stack frame being sure to preserve the return value.
   #CALL
   '''
   returnValue = SS.pop( )     # Save a copy of the return value
   CS, CP, SP, BP, BINF = BINF # Restore the caller's stack frame
   del SS[ SP : ]         # Pop all of the caller's arguments
   SS.append( returnValue )    # Restore the return value to the top of the stack

def op_RETv( ):
   '''RET <return value>
   SS:  [ ..., <old stack frame>, <current stack frame> ]  ->  [ ..., <old stack frame>, <return value> ]
   :    Restore the prior stack frame being sure to preserve the return value.
   :    Convenience.  Equivalent to: PUSH <return value>; RET;
   #CALL CONVENIENCE
   '''
   returnValue = CS[ CP + 1 ]
   CS, CP, SP, BP, BINF = BINF # Restore the caller's stack frame
   del SS[ SP : ]         # Pop all of the caller's arguments
   SS.append( returnValue )    # Restore the return value to the top of the stack

def op_PUSH_BPOFF( ):
   '''PUSH_BPOFF <offest>
   SS:  [ ... ]  ->  [ ..., <value> ]
   :    Push the item at the indicated offset from the Base Pointer.
   :    e.g. -1 pushes the stack item at stack index [BP + <offset>],
   :    which is the first arguemnt to the current stack frame.
   #CALL
   '''
   offset = CS[ CP + 1 ]
   SS.append( SS[BP + offset] )
   CP += 2

def op_CALLp( ):
   '''CALLP
   SS:  [ ..., <python function> ]  ->  [ ... ]
   :    Call the python function.
   #CALLP
   '''
   pyFn       = SS.pop()
   numArgs    = CS[CP+1]
   
   oldCP      = CP
   try:
      pyFn(  numArgs )
   except:
      FLG = UNKNOWN_UNRECOVERABLE
   if CP == oldCP:
      CP += 2

# Basic Branching
def op_HALT( ):
   '''HALT
   : Terminate the current process.
   #BRANCH'''
   raise INTERRUPT( 'HALT' )
   #FLG = HALT
   #CP += 1

def op_JMP( ):
   '''JMP <address>
   :    Set the CP to <address>.
   #BRANCH
   '''
   JUMP_OP( )

def op_JMP_T( ):
   '''JMP_T <address>
   SS:  [ ..., <value> ]  ->  [ ... ]
   :    Set the CP to <address>, if <value> is true.
   #BRANCH
   '''
   CJUMP_OP( lambda x: x == True )

def op_JMP_F( ):
   '''JMP_F <address>
   SS:  [ ..., <value> ]  ->  [ ... ]
   :    Set the CP to <address>, if <value> is false.
   #BRANCH
   '''
   CJUMP_OP( lambda x: x == False )

# Boolean Operations
def op_bNOT( ):
   '''bNOT
   SS:  [ ..., <value> ]  ->  [ ..., (boolean-not <value>) ]
   :    Unary-op; pop 1 arg, compute boolean-not from popped args, push result.
   #ALU.BOOLEAN
   '''
   BINARY_OP( op.not_, bool )

def op_bAND( ):
   '''bAND
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> boolean-AND <value2>) ]
   :    Binary-op; pop 2 args, compute boolean-and from popped args, push result.
   #ALU.BOOLEAN
   '''
   BINARY_OP( lambda x,y: x and y, bool, bool )

def op_bOR( ):
   '''bOR
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> boolean-OR <value2>) ]
   :    Binary-op; pop 2 args, compute boolean-or from popped args, push result.
   #ALU.BOOLEAN
   '''
   BINARY_OP( lambda x,y: x or y, bool, bool )

# Bitwise Operations
def op_iNEG( ):
   '''iNEG
   SS:  [ ..., <value> ]  ->  [ ..., (bitwise-neg <value>) ]
   :    Unary-op; pop 1 arg, compute bitwise-negation from popped args, push result.
   #ALU.BITS
   '''
   BINARY_OP( op.invert, int )

def op_iAND( ):
   '''iAND
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> bitwise-AND <value2>) ]
   :    Binary-op; pop 2 args, compute bitwise-and from popped args, push result.
   #ALU.BITS
   '''
   BINARY_OP( op.and_, int, int )

def op_iOR( ):
   '''iOR
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> bitwise-OR <value2>) ]
   :    Binary-op; pop 2 args, compute bitwise-or from popped args, push result.
   #ALU.BITS
   '''
   BINARY_OP( op.or_, int, int )

def op_iXOR( ):
   '''iXOR
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> bitwise-XOR <value2>) ]
   :    Binary-op; pop 2 args, compute bitwise-xor from popped args, push result.
   #ALU.BITS
   '''
   BINARY_OP( op.xor, int, int )

def op_iSHL( ):
   '''iSHL
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> bitwise-XOR <value2>) ]
   :    Binary-op; pop 2 args, compute bitwise shift-left from popped args, push result.
   #ALU.BITS
   '''
   BINARY_OP( op.lshift, int, int )

def op_iSHR( ):
   '''iSHR
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> bitwise-XOR <value2>) ]
   :    Binary-op; pop 2 args, compute bitwise shift-right from popped args, push result.
   #ALU.BITS
   '''
   BINARY_OP( op.rshift, int, int )

# Integer Oprations
def op_iABS( ):
   '''iABS
   SS:  [ ..., <value> ]  ->  [ ..., (absolute-value <value>) ]
   :    Unary-op; pop 1 arg, compute absolute value from popped args, push result.
   #ALU.INTEGER
   '''
   UNARY_OP( abs, int )

def op_iCHSIGN( ):
   '''iCHSIGN
   SS:  [ ..., <value> ]  ->  [ ..., (-1 * <value>) ]
   :    Unary-op; pop 1 arg, compute numerical negation from popped args, push result.
   #ALU.INTEGER
   '''
   UNARY_OP( op.neg, int )

def op_iPROMOTE( ): # int -> float
   '''iPROMOTE
   SS:  [ ..., <value> ]  ->  [ ..., (convert-to-float <value>) ]
   :    Unary-op; pop 1 arg, compute floating pointer equivalent, push result.
   #ALU.INTEGER
   '''
   UNARY_OP( float, int )

def op_iEQ( ):
   '''iEQ
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> == <value2>) ]
   :    Binary-op; pop 2 args; compute integer equality; push bolean result.
   #ALU.INTEGER
   '''
   BINARY_OP( op.__eq__, int, int )

def op_iNE( ):
   '''iNE
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> != <value2>) ]
   :    Binary-op; pop 2 args; compute integer inequality; push bolean result.
   #ALU.INTEGER
   '''
   BINARY_OP( op.__ne__, int, int )

def op_iGT( ):
   '''iGT
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> > <value2>) ]
   :    Binary-op; pop 2 args; compute integer inequality; push result.
   #ALU.INTEGER
   '''
   BINARY_OP( op.__gt__, int, int )

def op_iGE( ):
   '''iGE
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> >= <value2>) ]
   :    Binary-op; pop 2 args; compute integer inequality; push bolean result.
   #ALU.INTEGER
   '''
   BINARY_OP( op.__ge__, int, int )

def op_iLT( ):
   '''iLT
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> < <value2>) ]
   :    Binary-op; pop 2 args; compute integer inequality; push bolean result.
   #ALU.INTEGER
   '''
   BINARY_OP( op.__lt__, int, int )

def op_iLE( ):
   '''iLE
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> <= <value2>) ]
   :    Binary-op; pop 2 args; compute integer inequality; push bolean result.
   #ALU.INTEGER
   '''
   BINARY_OP( op.__le__, int, int )

def op_iINC( ):
   '''iINC
   SS:  [ ..., <value> ]  ->  [ ..., (<value> + 1) ]
   :    Unary-op; pop 1 arg; compute integer increment; push result.
   #ALU.INTEGER
   '''
   SS[-1] += 1
   CP += 1

def op_iDEC( self ):
   '''iDEC
   SS:  [ ..., <value> ]  ->  [ ..., (<value> - 1) ]
   :    Unary-op; pop 1 arg; compute integer decrement; push result.
   #ALU.INTEGER
   '''
   self.SS[-1] -= 1
   self.CP += 1

def op_iADD( self ):
   '''iADD
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> + <value2>) ]
   :    Binary-op; pop 2 args; compute integer sum; push result.
   #ALU.INTEGER
   '''
   SS = self.SS
   SS[-1] = int(SS.pop()) + int(SS[-1])
   self.CP += 1

def op_iSUB( self ):
   '''iSUB
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> - <value2>) ]
   :    Binary-op; pop 2 args; compute integer difference; push result.
   #ALU.INTEGER
   '''
   SS = self.SS
   arg2 = SS.pop( )
   SS[-1] = SS[-1] - arg2
   #SS[-1] = int(SS[-1]) - int(arg2)
   #SS[-1] = (lambda x: int(SS[-1]) - x)(int(SS.pop()))
   self.CP += 1

def op_iMUL( self ):   
   '''iMUL
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> * <value2>) ]
   :    Binary-op; pop 2 args; compute integer product; push result.
   #ALU.INTEGER
   '''
   self.BINARY_OP( op.mul, int, int )

def op_iDIV( self ):
   '''iMUL
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> / <value2>) ]
   :    Binary-op; pop 2 args; compute integer ratio; push result.
   #ALU.INTEGER
   '''
   self.BINARY_OP( op.floordiv, int, int )

def op_iMOD( self ):
   '''iMUL
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> modulo <value2>) ]
   :    Binary-op; pop 2 args; compute integer remainder; push result.
   #ALU.INTEGER
   '''
   self.BINARY_OP( op.mod, int, int )

# IEEE Float Operations
def op_fABS( self ):
   '''FABS
   SS:  [ ..., <value> ]  ->  [ ..., (absolute-value <value>) ]
   :    Unary-op; pop 1 arg, compute absolute value from popped args, push result.
   #ALU.FLOAT
   '''
   self.UNARY_OP( abs, float )

def op_fCHSIGN( self ):
   '''ICHSIGN
   SS:  [ ..., <value> ]  ->  [ ..., (-1 * <value>) ]
   :    Unary-op; pop 1 arg, compute numerical negation from popped args, push result.
   #ALU.FLOAT
   '''
   self.UNARY_OP( op.neg, float )

def op_fDEMOTE( self ):  # float -> int
   '''FDEMOTE
   SS:  [ ..., <value> ]  ->  [ ..., (convert-to-integer <value>) ]
   :    Unary-op; pop 1 arg, compute integer equivalent, push result.
   #ALU.FLOAT
   '''
   self.UNARY_OP( int, float )

def op_fFRAC( self ):
   '''FFRAC
   SS:  [ ..., <value> ]  ->  [ ..., (fractionalPartOf <value>) ]
   :    Unary-op; pop 1 arg, compute fractional portion of, push result.
   #ALU.FLOAT
   '''
   self.UNARY_OP( lambda x:x - int(x), float )

def op_fEQ( self ):
   '''FEQ
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> == <value2>) ]
   :    Binary-op; pop 2 args; compute equality; push bolean result.
   #ALU.FLOAT
   '''
   self.BINARY_OP( op.__eq__, float, float )

def op_fNE( self ):
   '''FNE
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> != <value2>) ]
   :    Binary-op; pop 2 args; compute float inequality; push bolean result.
   #ALU.FLOAT
   '''
   self.BINARY_OP( op.__ne__, float, float )

def op_fGT( self ):
   '''fGT
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> > <value2>) ]
   :    Binary-op; pop 2 args; compute float inequality; push result.
   #ALU.FLOAT
   '''
   self.BINARY_OP( op.__gt__, float, float )

def op_fGE( self ):
   '''fGE
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> >= <value2>) ]
   :    Binary-op; pop 2 args; compute float inequality; push bolean result.
   #ALU.FLOAT
   '''
   self.BINARY_OP( op.__ge__, float, float )

def op_fLT( self ):
   '''fLT
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> < <value2>) ]
   :    Binary-op; pop 2 args; compute float inequality; push bolean result.
   #ALU.FLOAT
   '''
   self.BINARY_OP( op.__lt__, float, float )

def op_fLE( self ):
   '''fLE
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> <= <value2>) ]
   :    Binary-op; pop 2 args; compute float inequality; push bolean result.
   #ALU.FLOAT
   '''
   self.BINARY_OP( op.__le__, float, float )

def op_fADD( self ):
   '''fADD
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> + <value2>) ]
   :    Binary-op; pop 2 args; compute float sum; push result.
   #ALU.FLOAT
   '''
   self.BINARY_OP( op.__add__, float, float )

def op_fSUB( self ):
   '''fSUB
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> - <value2>) ]
   :    Binary-op; pop 2 args; compute float difference; push result.
   #ALU.FLOAT
   '''
   self.BINARY_OP( op.__sub__, float, float )

def op_fMUL( self ):   
   '''fMUL
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> * <value2>) ]
   :    Binary-op; pop 2 args; compute float product; push result.
   #ALU.FLOAT
   '''
   self.BINARY_OP( op.__mul__, float, float )

def op_fDIV( self ):
   '''fDIV
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> / <value2>) ]
   :    Binary-op; pop 2 args; compute float ratio; push result.
   #ALU.FLOAT
   '''
   self.BINARY_OP( op.__div__, float, float )

def op_fPOW( self ):
   '''fPOW
   SS:  [ ..., <value2>, <value1> ]  ->  [ ..., (<value1> ^ <value2>) ]
   :    Binary-op; pop 2 args; compute float power; push result.
   #ALU.FLOAT
   '''
   self.BINARY_OP( op.pow, float, float )

def op_fLOG( self ):
   '''fLOG
   SS:  [ ..., <base>, <x> ]  ->  [ ..., (log <base> <x>) ]
   :    Binary-op; pop 2 args; compute float log; push result.
   #ALU.FLOAT
   '''
   self.BINARY_OP2( op.log, float, float )

def op_fSIN( self ):
   '''fSIN
   SS:  [ ..., <theta> ]  ->  [ ..., (sine <theta>) ]
   :    Unary-op; pop 1 arg; compute sine; push result.
   #ALU.FLOAT
   '''
   self.UNARY_OP( math.sin, float )

def op_fASIN( self ):
   '''fASIN
   SS:  [ ..., <theta> ]  ->  [ ..., (arcsine <theta>) ]
   :    Unary-op; pop 1 arg; compute arcsine; push result.
   #ALU.FLOAT
   '''
   self.UNARY_OP( math.asin, float )

def op_fCOS( self ):
   '''fCOS
   SS:  [ ..., <theta> ]  ->  [ ..., (cosine <theta>) ]
   :    Unary-op; pop 1 arg; compute cosine; push result.
   #ALU.FLOAT
   '''
   self.UNARY_OP( math.cos, float )

def op_fACOS( self ):
   '''fACOS
   SS:  [ ..., <theta> ]  ->  [ ..., (arccosine <theta>) ]
   :    Unary-op; pop 1 arg; compute arccosine; push result.
   #ALU.FLOAT
   '''
   self.UNARY_OP( math.acos, float )

def op_fTAN( self ):
   '''fTAN
   SS:  [ ..., <theta> ]  ->  [ ..., (tangent <theta>) ]
   :    Unary-op; pop 1 arg; compute tangent; push result.
   #ALU.FLOAT
   '''
   self.UNARY_OP( math.tan, float )

def op_fTAN2( self ):
   '''fATAN
   SS:  [ ..., <y>, <x> ]  ->  [ ..., (arctangent (<y>/<x>)) ]
   :    Binary-op; pop 2 args; compute arctangent; push result.
   #ALU.FLOAT
   '''
   self.BINARY_OP( math.atan2, float, float )

def op_fATAN( self ):
   '''fATAN
   SS:  [ ..., <theta> ]  ->  [ ..., (arctangent <theta>) ]
   :    Unary-op; pop 1 arg; compute arctangent; push result.
   #ALU.FLOAT
   '''
   self.UNARY_OP( math.atan, float )

# String Manipulation
def op_sEQ( self ):
   pass

def op_sNE( self ):
   pass

def op_sGT( self ):
   pass

def op_sGE( self ):
   pass

def op_sLT( self ):
   pass

def op_sLE( self ):
   pass

def op_sLEN( self ):
   '''sLEN
   SS:  [ ..., <val:str> ]  ->  [ ..., (len <val:str>):int ]
   :    Unary-op; pop 1 arg; compute string length; push result.
   #ALU.STRING
   '''
   theString = self.SS[-1]
   self.SS[-1] = len(theString)
   self.CP += 1

def op_sAT( self ):     # [ ..., string, index ]  =>  [ ..., character ]
   '''sAT
   SS:  [ ..., <val:str>, <index:int> ]  ->  [ ..., (<val>[ <index> ]):str ]
   :    Binary-op; pop 2 args; compute substring at index; push result.
   #ALU.STRING
   '''
   index = self.SS.pop()
   theString = self.SS[ -1 ]
   self.SS[ -1 ] = theString[index]
   self.CP += 1

def op_sCAT( self ):
   '''sAT
   SS:  [ ..., <val2:str>, <val1:str> ]  ->  [ ..., (<val1> + <val2>):str ]
   :    Binary-op; pop 2 args; compute concatenation; push result.
   #ALU.STRING
   '''
   string2 = self.SS.pop()
   string1 = self.SS[-1]
   self.SS[-1] = string1 + string2
   self.CP += 1

def op_sJOIN( self ):
   '''sAT
   SS:  [ ..., [<val1:str>, <val2:str>, ...], <sep:str> ]  ->  [ ..., (<val1> + <sep> + <val2> + <sep> + ...):str ]
   :    Binary-op; pop 2 args; compute join; push result.
   #ALU.STRING
   '''
   joinStr = self.SS.pop()
   strList = self.SS[-1]
   self.SS[-1] = joinStr.join( *strList )
   self.CP += 1

def op_sSPLIT( self ):
   '''sSPLIT
   SS:  [ ..., <val:str>, <index:int> ]  ->  [ ..., <val>[:<index>], <val>[<index>:] ]
   :    Binary-op; pop 2 args; compute split; push substrings.
   #ALU.STRING
   '''
   index = self.SS.pop()
   theString = self.SS[-1]
   start = theString[ : index ]
   end   = theString[ index : ]
   self.SS[-1] = start
   self.SS.push(end)
   self.CP += 1

def op_sTOINT( self ):  # [ ..., string ]  =>  [ ..., int(string) ]
   theString = self.SS[-1]
   self.SS[-1] = int(theString)
   self.CP += 1

def op_sTOFLOAT( self ): # [ ..., string ]  =>  [ ..., float(string) ]
   theString = self.SS[-1]
   self.SS[-1] = float(theString)
   self.CP += 1

# List Operations
def op_lPACK( self ):       # [ obj1, obj2, ... objCount ]  =>  [ ..., [obj1, obj2, ...] ]
   count  = self.SS.pop( )
   values = self.SS[ 0 - count : ]
   del self.SS[ 0 - count - 1 : ]
   self.SS.append( values )
   self.CP += 1

def op_lUNPACK( self ):     # [ list ] <- SP   =>   [ list-contents ] <- SP
   values = self.SS.pop( )
   count  = len(values)
   values.append( count )
   self.SS.extend( values )
   self.CP += 1

def op_lREVERSE( self ):    # [ ..., list ]  =>  [ ..., reversed(list) ]
   theList = self.SS[-1].reverse()
   self.CP += 1

def op_lLEN( self ):        # [ ..., list ]  =>  [ ..., len(list) ]
   theList = self.SS[ -1 ]
   self.SS[-1] = len(theList)
   self.CP += 1

def op_lAT( self ):         # [ list, list-index ] <- SP  =>  [ list, list-item ]
   index = self.SS[ -1 ]
   aList = self.SS[ -2 ]
   self.SS[ -1 ] = aList[ index ]
   self.CP += 1

def op_lATSET( self ):      # [ list, list-index, newValue ]  ;; modify list at list-index with newValue
   newValue = self.SS.pop( )
   index    = self.SS.pop( )
   theList  = self.SS[ -1 ]
   theList[ index ] = newValue
   self.CP += 1

def op_lPUSH( self ):       # [ list, newItem ]
   newItem  = self.SS.pop( )
   theList  = self.SS[ -1 ]
   theList.push( newItem )
   self.CP += 1

def op_lPOP( self ):        # [ list ]  =>  [ oldListTop ]
   theList  = self.SS[ -1 ]
   value    = theList.pop( )
   self.SS.append( value )
   self.CP += 1

def op_lCAT( self ):        # [ list1, list2 ]  => [ <list-1-contents> <list-2-contents> ]
   list2 = self.SS.pop()
   list1 = self.SS[ -1 ]
   self.SS[ -1 ] = list1 + list2
   self.CP += 1

def op_lSPLIT( self ):      # [ ..., aList, size ]  =>  [ ..., aList[ : size ], aList[ size : ] ]
   count = self.SS.pop( )
   theList = self.SS[ -1 ]
   self.SS[ -1 ] = theList[ : count ]
   self.SS.append( theList[ count : ] )
   self.CP += 1

def op_lCOPY( self ):
   top = self.SS[ -1 ]
   top = copy.copy( top )
   self.SS.push( top )
   self.CP += 1

def op_lSWAPSTACK( self ):  # [ ..., stack-A ] => [ ..., oldStack ]
   '''SWAPSTACK
   SS = currentStack           SS = alternateStack
   [..., alternateStack ]  =>  [ ..., currentStack ]
   '''
   newStack = self.SS.pop( )
   oldStack = self.SS
   self.SS = newStack
   newStack.push( oldStack )
   self.CP += 1

def op_lPUSHNEWLIST( self ):      # push a new empty list onto the stack.
   self.SS.push( list() )
   self.CP += 1


import threading
import time
from queue import PriorityQueue

class Agent( threading.Thread ):
   requestID = 0
   
   def __init__( self, requestsQueue, resultsQueue, **kwds ):
      super().__init__( **kwds )
      self.setDaemon( 1 )
      self.workRequestQueue = PriorityQueue
      self.resultQueue      = PriorityQueue
      self.start( )
   
   def performWork( self, priority, callable, *args, **kwds ):
      Agent.requestID += 1
      self.workRequestQueue.put( (priority, (Agent.requestID, callable, args, kwds)) )
      return Agent.requestID

   def run( self ):
      while True:
         priority, request = self.workRequestQueue.get( )
         requestID, callable, args, kwds = request
         self.resultQueue.put( (requestID, callable(*args,**kwds)) )

def systemClockAgent( seconds=0.10 ):
   time.sleep( seconds )
   return 'clock-tick'
   

class InterruptableStackVM( StackVM1 ):
   def __init__( self ):
      super().__init__( )
 
   def run( self, CS ):
      self.reboot( CS )
      while True:
         self.handleIRQ( )
         self.IR = self.CS[ self.CP ]
         func = getattr( self, 'op_' + self.IR )
         func( )
         
         if self.FLG != 0:
            if self.FLG == self.HALT:
               break
   
   def handleIRQ( self ):
      irq,payload = self.IRQ.get( )
      
      func = getattr( self, 'irq_' + self.irq )
      func(payload)
  
   def reboot( self, CS, SS=None, ENV=None ):
      super().reboot( CS, SS, ENV )
      
      self.IRQ     = [ ]                       # Interrupts
      self.IV      = [ ]                       # Interrupt Handler Vector

   def op_IRQ_SEND( self ):
      '''Generate an interrupt request.'''
      pass
   
   def op_IRQ_SUSPEND( self ):
      '''Suspend interrupt handling.'''
      pass
   
   def op_IRQ_RESUME( self ):
      '''Resume interrupt handling.'''
      pass
   
   def irq_1( self, payload ):
      pass
   
   def irq_2( self, payload ):
      pass
   


def parseDoc( aDoc ):
   docIter     = iter(aDoc.splitlines())
   usage       = next(docIter)
   stackDoc    = ('','')
   descr       = ''
   cat         = ''
   try:
      op,sep,rest = docIter.partition(' ')
   except:
      op = usage
   
   for line in docIter:
      line = line.strip()
      if line.startswith( 'SS:' ):
         line = line[3:].strip()
         stackBefore, sep, stackAfter = line.partition( '->' )
         stackBefore = stackBefore.strip()
         stackAfter  = stackAfter.strip()
         stackDoc    = (stackBefore,stackAfter)
      elif line.startswith( ':' ):
         descr       = line[1:].strip()
      elif line.startswith( '#' ):
         cat         = line[1:].strip()
   return (op,usage,stackDoc,descr,cat)

def assemble( aProg ):
   # Two-Pass Assembler
   codeSeg     = [ ]
   localLabels = { }
   
   # Pass 1 - Catalog Labels
   address = 0
   for line in aProg:
      opcode   = line[0]
      operands = line[1:]
      if isinstance( opcode, str ) and (opcode[-1] == ':'):
         localLabels[opcode] = address
         
         opcode   = line[1]
         operands = line[2:]
      
      address += 1 + len(operands)

   # Pass 2 - Replace Jump Labels
   for address,line in enumerate(aProg):
      opcode   = line[0]
      operands = line[1:]
      if isinstance( opcode, str ) and (opcode[-1] == ':'):
         opcode   = line[1]
         operands = line[2:]
      
      codeSeg.append( opcode )
      
      for operand in operands:
         if isinstance( operand, str ) and (operand[-1] == ':'):
            operand = localLabels[operand]
         
         codeSeg.append( operand )

   return codeSeg

def dissassemble( codeSeg, opcodes, hexintegers=False ):
   CS      = codeSeg
   opcodes = [ code.upper() for code in opcodes ]
   lines   = [ ]

   address = 0
   tok     = CS[address]
   try:
      while tok.upper() in opcodes:
         newLine = [ address, tok ]
         lines.append( newLine )
         address += 1
         tok = CS[address]
         while (not isinstance(tok,str)) or (tok.upper() not in opcodes):
            newLine.append( tok )
            address += 1
            tok = CS[address]
   except IndexError:
      pass
   
   for addr, opCode, *args in lines:
      if hexintegers:
         argStrs = [ hex(val).upper() if isinstance(val,int) else str(val) for val in args ]
      else:
         argStrs = [ str(val) for val in args ]
      
      try:
         argStr = ', '.join(argStrs)
      except:
         argStr = ''
   
      if hexintegers:
         print( '{:x6X}: {:10s}   {:22s}'.format(addr, opCode, argStr) )
      else:
         print( '{:06d}: {:10s}   {:22s}'.format(addr, opCode, argStr) )


 
import functools
class CodeObject1( object ):
   def __init__( self, opCodeMap, src=None, opt=None, obj=None, exe=None, labels=None, refs=None ):
      self.opCodeMap = opCodeMap
      self.set( src,opt,obj,exe,labels,refs )
   
   def set( self, src=None, opt=None, obj=None, exe=None, labels=None, refs=None ):
      if src is None:
         src = ''
      
      if opt is None:
         opt = [ ]
      
      if obj is None:
         obj = [ ]
      
      if exe is None:
         exe = [ ]
      
      if labels is None:
         labels = { }
      
      if refs is None:
         refs = { }
      
      # Source Code Support
      self.sourceCode     = src
      
      # Optimized Source Code Support
      self.optimizedCode  = opt
      
      # Assembled Object Code Support
      self.objectCode     = obj
      self.staticLabels   = labels
      self.staticRefs     = refs
      
      # Executable Code Support
      self.executableCode = exe

   def optimize( self ):  # src -> opt
      # Clear generated objects.
      # If assembly fails for some reason these will still be valid
      self.optimizedCode  = [ ]
      self.objectCode     = [ ]
      self.executableCode = [ ]
      self.staticLabels   = { }
      self.staticRefs     = { } 
      
      # Temporaries to hold the optimized code
      optimizedCode       = [ ]
      
      # Main Optimization Loop
      opt = Optimizer()
      self.optimizedCode = opt.optimize( self.sourceCode )
   
      # If optimization didn't fail, reassign
      self.optimizedCode  = optimizedCode
   
   def assemble( self ):  # src|opt -> obj
      # Clear generated objects.
      # If assembly fails for some reason these will still be valid
      self.objectCode     = [ ]
      self.executableCode = [ ]
      self.staticLabels   = { }
      self.staticRefs     = { } 
      
      # Temporaries to hold the generated code
      objectCode          = [ ]
      staticLabels        = { }     # Map:  label:str -> address
      staticRefs          = { }     # Map:  label:str -> [ <reference offset> ]
      
      if len(self.optimizedCode) > 0:
         source = self.optimizedCode
      else:
         source = self.sourceCode
   
      # Assembly Main Loop
      address = 0
      for line in source:
         idx = 0
         try:
            opcode  = line[idx]
            idx += 1
         except:
            continue
         
         if isinstance( opcode, str ) and (opcode[-1] == ':'):
            staticLabels[opcode] = address
            
            try:
               opcode = line[idx]
               idx += 1
            except:
               continue
         
         objectCode.append( opcode )
         address += 1
         
         try:
            operand = line[idx]
         except:
            continue
         
         if isinstance(operand, str):
            staticRefs.setdefault(operand,[]).append(address)
         
         objectCode.append( operand )
         address += 1

      # If assembly didn't fail, we can reassign
      self.objectCode     = objectCode
      self.staticLabels   = staticLabels
      self.staticRefs     = staticRefs
   
   def link( self ):      # obj -> exe
      # Clear generated objects.
      # If linking fails for some reason these will still be valid
      self.executableCode = [ ]
      
      # Temporaries to hold the generated code
      exe = self.objectCode[:]
      
      # Linker Main Loop
      for label,refList in self.staticRefs.items():
         try:
            address = self.staticLabels[label]
            for refAddr in refList:
               exe[refAddr] = address
         except:
            pass
      
      # If linking didn't fail we can reassign
      self.executableCode = exe
   
   @staticmethod
   def frozenCall( opCodeMap, opcode, arg ):
      op = opCodeMap[opcode]
      def fn( ):
         op( arg )
      return fn
      #return lambda x=arg: op(x)
   
   def partialize( self ):
      newExe = [ ]
      
      for item in self.executableCode:
         #ptfn = CodeObject.frozenCall( self.opCodeMap, opcode, *operands )
         #newExe.append( ptfn )
         try:
            item_fn = self.opCodeMap[item]
         except:
            item_fn = item
         newExe.append( item_fn )
      
      self.executableCode = newExe
   
   def pipeline( self, address, sentinel=('HALT', 'JMP*', 'CALL*', 'RET') ):
      pass
   
   def __getitem__( self, address ):
      return self.executableCode[ address ]

   def dissassemble( self, which='exe' ):
      if which in ( 'src','opt' ):
         if (which == 'src') and isinstance( self.sourceCode, str ):
            return self.sourceCode
         
         toDis = self.sourceCode if which == 'src' else self.optimizedCode
         return self._dis_src( toDis )
      
      if which == 'obj':
         if len(self.optimizedCode) > 0:
            return dissassemble( which='opt' )
         elif len(self.sourceCode) > 0:
            return dissassemble( which='src' )
         else:
            return self._dis_src( self.objectCode )
      
      if which == 'exe':
         if len(self.optimizedCode) > 0:
            return dissassemble( which='opt' )
         elif len(self.sourceCode) > 0:
            return dissassemble( which='src' )
         else:
            return self._dis_exe()
      
      raise NotImplemented()
   
   def _dis_src( self, aSrc ):
      raise NotImplemented()
      

   def _dis_exe_( self ):
      raise NotImplemented()      

class Optimizer( object ):
   def __init__( self ):
      self._stack = [ ]
      self._opts  = { }
   
   def stack( self ):
      return self._stack

   def optimize( self, source, **flags ):
      src = source[:]
      defaultFlags = { stk:True for stk in self._stack }
      defaultFlags.update( flags )
      
      for optName in self._stack:
         if defaultFlags[optName]:
            opt = self._opts[optName]
            opt.optimize(src)
      
      return src

class PeepholeOptimizer( object ):
   def __init__( self ):
      pass
   
   def optimize( self, source, **flags ):
      pass

if __name__ == '__main__':
   vm = StackVM1( )
   fib = CodeObject1( vm.opcodes, src=[               # [ ..., arg ]
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH',                  2 ],
      [                  'iGT'                      ],
      [                  'JMP_T',           'else:' ],
      [                  'RETv',                  1 ],
      [ 'else:',         'PUSH_BPOFF',           -1 ],
      [                  'iDEC'                     ],
      [                  'CALLr',                 1 ],   # Recursive call
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH',                  2 ],
      [                  'iSUB'                     ],
      [                  'CALLr',                 1 ],   # Recursive call
      [                  'iADD'                     ],
      [ 'end:',          'RET'                      ]
   ] )
   fib.assemble( )
   fib.link( )
   fib.partialize( )

   dbl = [
      [                  'PUSH_BPOFF',            0 ],
      [                  'PUSH',                  2 ],
      [                  'iMUL'                     ],
      [                  'RET'                      ]
   ]
   dbl_exe = assemble( dbl )
   
   _ = None
   sqr = [
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH_BPOFF',           -1 ],
      [                  'iMUL'                     ],
      [                  'RET'                      ]
   ]
   sqr_exe = assemble( sqr )
   
   def fact( n ):
      if n == 0:
         return 1
      else:
         return n * fact(n - 1)

   fct = [
      [                  'PUSH_BPOFF',            0 ],
      [                  'PUSH',                  0 ],
      [                  'iCMP'                     ],
      [                  'JMP_NE',          'else:' ],
      [                  'RETv',                  1 ],
      [ 'else:',         'PUSH_BPOFF',            0 ],
      [                  'PUSH_BPOFF',            0 ],
      [                  'iDEC'                     ],
      [                  'CALLr',                 1 ],
      [                  'iMUL'                     ],
      [ 'end:',          'RET'                      ]
   ]
   fct_exe = assemble( fct )
   
   prog = CodeObject1( vm.opcodes, src=[
      [                  'PUSH',                  20 ],
      [                  'PUSH',  fib.executableCode ],   # push the function
      [                  'CALL',                   1 ],   # call the function
      [                  'HALT'                      ]
   ] )
   prog.optimize( )
   prog.assemble( )
   prog.link( )
   prog.partialize( )
   
   from util_profile import PerfTimer
   
   entryPoint = prog.executableCode
   
   intructionCount = 0
   with PerfTimer( ):
      vm.run_p( entryPoint )   
      #instructionCount = vm.run_withTrace( entryPoint )

   print( vm.SS.pop() )
   PerfTimer.dump( )
   #if instructionCount > 0:
      #print( 'Number of vm instructions executed: {:d}.'.format(instructionCount))
   
   
   
   