#!python3.5

import ltk_py3.Listener as Listener
from LypsParser import LypsParser
from LypsImpl import LEnv, evalLypsExpr, beautifyLypsExpr
import sys

from LypsWalkingInterp import *
from LypsCompiler import *
from ltk_py3.stackvm1 import *
from ltk_py3.stackvm2 import *
from ltk_py3.stackvm3 import *
from time import process_time

class LypsInterpreter( object ):
   def __init__( self ):
      super().__init__( )
      self._parser = LypsParser( )
      self._comp   = LypsCompiler( )
      self._vm     = StackVM1( )
      self._vm2    = StackVM2( )
      self._globalEnvironment = LypsCompiler.defaultEnv( )

   def reboot( self, fileReader=None ):
      self._vm     = StackVM1( )
      self._vm2    = StackVM2( )
      self._globalEnvironment = LypsCompiler.defaultEnv( )
      self._vm.doc_instructionSet( )

   def eval( self, inputExprStr, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr ):
      inputExpr = self._parser.parse( inputExprStr )
      
      compiledExpr = self._comp.compile( self._globalEnvironment, inputExpr )
      expr_exe = assemble( compiledExpr )
      which = 0
      hexintegers = True
      if which == 0:
         resultExpr = self._vm.run( expr_exe, self._globalEnvironment )
      elif which == 1:
         self._vm.reloadLib( self._globalEnvironment )
         resultExpr = self._vm.ll_run( expr_exe, self._globalEnvironment )
      elif which == 2:
         print( 'Dissassembly of the Code Segment:')
         dissassemble( expr_exe, self._vm.opcodes, hexintegers=True )
         print( '==============================================================' )
         print( )
         for instructionNum,vmState in enumerate(self._vm.iterrun( expr_exe, self._globalEnvironment )):
            vmState._trace( instructionNum, hexintegers=True )
         resultExpr = self._vm.last
      elif which == 3:
         start = process_time()
         resultExpr1 = self._vm.run( expr_exe, self._globalEnvironment )
         cost = process_time() - start
         if cost == 0.0:
            cost = 1e-10
      
         for instructionNum,vmState in enumerate(self._vm.iterrun( expr_exe, self._globalEnvironment )):
            pass
         resultExpr = self._vm.last
         instructionsPerSec = instructionNum / cost
         print( '==============================================================' )
         print( '   Total Instructions executed:    {:012d}'.format(instructionNum)        )
         print( '   Total Execution Time:           {:15.5f} seconds'.format(cost) )
         print( '   Instructions Per Second:        {:9.3f}'.format(instructionsPerSec) )
         print( '   MIPS:                           {:9.6f}'.format(instructionsPerSec/1000000.0))
      elif which == 4:
         start = process_time()
         resultExpr1 = self._vm.run( expr_exe, self._globalEnvironment )
         cost = process_time() - start
         if cost == 0.0:
            cost = 1e-10
      
         for instructionNum,vmState in enumerate(self._vm.iterrun( expr_exe, self._globalEnvironment )):
            pass
         resultExpr = self._vm.last
         instructionsPerSec = instructionNum / cost
         print( '==============================================================' )
         print( '   Total Instructions executed:    {:012d}'.format(instructionNum)        )
         print( '   Total Execution Time:           {:15.5f} seconds'.format(cost) )
         print( '   Instructions Per Second:        {:9.3f}'.format(instructionsPerSec) )
         print( '   MIPS:                           {:9.6f}'.format(instructionsPerSec/1000000.0))
      return beautifyLypsExpr( resultExpr )

   def runtimeLibraries( self ):
      return [ ]
      #return [ 'Lybrary.lyps' ]

   def testFileList( self ):
      return [ 'test0001.lyps',
               'test0002.lyps' ]
'''
@LDefPrimitive( 'parse' )          # (parse <expressionString>)
def LP_parse( env, *args, **keys ):
   inputExprStr = args[0]
   parser = LypsParser( )
   return parser.parse( inputExprStr )

@LDefPrimitive( 'load' )
def LP_load( env, *args, **keys ):
   if len(args) != 1:
      print( '(load <filename>), to read and evaluate the contents of a Lyps file.\n' )
      return
   
   theFilename = args[0]
   if isinstance( theFilename, LSymbol ):
      theFilename = theFilename._val
   
   try:
      return theListener.readAndEvalFile( theFilename )
   except Exception as ex:
      return LNULL

'''
if __name__ == '__main__':
   interp = LypsInterpreter( )
   theListener = Listener.Listener( interp, language='Lyps',
                                            version='0.1',
                                            author='Ronald Provost')
   
   theListener.readEvalPrintLoop( )

