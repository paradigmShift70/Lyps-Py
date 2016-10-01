from LypsParser import *
from Listener import Listener, EvaluationError
from Scanner import ScannerLineStream
import Lyps
import io


class LypsListener( Listener ):
   def __init__( self ):
      super( ).__init__( )
      self._env     = LEnv( )
      self._parser  = LypsParser( )

   def parse( self, inputExprStr ):
      return self._parser.parse( inputExprStr )
   
   def eval( self, inputExpr ):
      if isinstance(inputExpr, L_ATOM):
         return inputExpr
      else:
         return inputExpr.eval( self._env )

   def parseAndEvalExpr( self, inputExprStr ):
      try:
         inputExpr = self.parse( inputExprStr )
         return self.eval( inputExpr )
  
      except ParseError as ex:
         print( ex.generateVerboseErrorString() )
  
      except EvaluationError as ex:
         print( ex.args[-1] )
  
      except Exception as ex:
         print( ex.args[-1] )
   
   def _parseAndEvalExpr( self, inputExprStr ):
      inputExpr = self.parse( inputExprStr )
      return self.eval( inputExpr )
   
   def _printable( self, expression ):
      if isinstance( expression, str ):
         return '"' + expression + '"'
      else:
         return str( expression )

   def execResetListenerCommand( self, cmdParts ):
      self.initialize( )

   def rebootExecutionEnvironment( self, listOfLibraries ):
      self._env = self._env.reInitialize( )
      
      for libFileName in listOfLibraries:
         self.readAndEvalFile( libFileName )

   def readAndEvalFile( self, filename, testFile=False ):
      file = open( filename, 'r' )
      if not file:
         self.writeLn( 'Unable to read file.\n' )
         return
      
      inputText = file.read()
      
      if testFile:
         print( '   Test file: {0}... '.format(filename), end='' )
         self._sessionLog_test( inputText )
      else:
         return self._sessionLog_restore( inputText )

   def _sessionLog_restore( self, inputText ):
      exprNum = 0
      
      for exprNum,exprPackage in enumerate(self.iterLog(inputText)):
         exprStr,outputStr,retValStr = exprPackage
         inputExpr = self.parse( exprStr )
         resultExpr = self.eval( inputExpr )
         exprNum += 1
      
      return exprNum
   
   def _sessionLog_test( self, inputText, verbosity=0 ):
      numPassed = 0
      
      if verbosity >= 3:
         print()
      
      try:
         for exprNum,exprPackage in enumerate(self.iterLog(inputText)):
            Lyps.L_STDOUT = io.StringIO()
            exprStr,expectedOutput,expectedRetValStr = exprPackage
            inputExpr = self.parse( exprStr )
            resultExpr = str(self.eval( inputExpr ))
         
            # Test stdio output
            outputText = Lyps.L_STDOUT.getvalue()
            if outputText == expectedOutput:
               outputTest_passed = True
               outputTest_reason = 'PASSED!'
            else:
               outputTest_passed = False
               outputTest_reason = 'Failed!  Output value doesn\'t equal expected value.'
         
            # Test Return Value
            if (resultExpr is None) and (expectedRetValStr is not None):
               retValTest_passed = False
               retValTest_reason = 'Failed!  Returned <Code>None</Code>; expected <i>value</i>.'
            elif (resultExpr is not None) and (expectedRetValStr is None):
               retValTest_passed = False
               retValTest_reason = 'Failed!  Returned a value; expected <Code>None</Code>'
            elif (resultExpr is not None) and (expectedRetValStr is not None):
               if resultExpr == expectedRetValStr:
                  retValTest_passed = True
                  retValTest_reason = 'PASSED!'
               else:
                  retValTest_passed = False
                  retValTest_reason = 'Failed!  Return value doesn\'t equal expected value.'
         
            # Determine Pass/Fail
            if outputTest_passed and retValTest_passed:
               test_passed = True
               test_reason = 'PASSED!'
               numPassed += 1
            else:
               test_passed = False
               test_reason = 'Failed!'
         
            if verbosity >= 3:
               print( '     {0}. {1}'.format(str(exprNum).rjust(6), test_reason) )
      
         Lyps.L_STDOUT = sys.stdout
      
         numTests = exprNum + 1
         numFailed = numTests - numPassed
         if test_passed:
            print( 'PASSED!' )
         else:
            print( '({0}/{1}) Failed.'.format(numFailed,numTests) )
         
      except:
         Lyps.L_STDOUT = sys.stdout
         raise
   
   def iterLog( self, inputText ):
      stream = ScannerLineStream( inputText )
      
      while True:
         # Skip empty and comment lines
         line = stream.peekLine()
         strippedLine = line.strip()
         while (strippedLine == '') or strippedLine.startswith( ';' ):
            stream.consumeLine()
            line = stream.peekLine()
            strippedLine = line.strip()
         
         if not line.startswith( '>>> ' ):
            raise Exception()
         
         # Parse Expression
         expr = line[ 4: ]
         stream.consumeLine()
         line = stream.peekLine()
         while line.startswith( '... ' ):
            expr += line[ 4: ]
            stream.consumeLine()
            line = stream.peekLine()
         
         output = None
         while not line.startswith( ('==> ','... ','>>> ') ):
            # Parse written output
            if output is None:
               output = ''
            output += line
            stream.consumeLine()
            line = stream.peekLine()
         if output:
            output = output[ : -1 ]        # remove the newline character at the end of output
         
         retVal = None
         if line.startswith( '==> ' ):
            retVal = line[ 4: ]
            stream.consumeLine()
            line = stream.peekLine()
            while not line.startswith( ('==> ','... ','>>> ') ):
               retVal += line
               stream.consumeLine()
               line = stream.peekLine()
            retVal = retVal[ : -2 ]       # remove the two newline characters at the end of retVal
         
         yield expr,output,retVal
   
   def _getTestfileList( self ):
      return [ 'test0001.lyps',
               'test0002.lyps' ]

STANDARD_LIBRARIES = [ 'Lybrary.lyps' ]

def bootLypsListenerInstance( lib=None, verbosity=3 ):
   if lib is None:
      lib = STANDARD_LIBRARIES
   
   if verbosity >= 1:
      print( 'Lyps Interpreter' )
   
   listener = LypsListener( )
   if verbosity >= 2:
      print( '- Execution environment initialized.' )
   
   listener.initialize( )
   
   for libName in lib:
      if verbosity >= 3:
         print( '- Loading runtime library: {0}'.format(libName), end='' )
      
      try:
         listener.parseAndEvalExpr( '(load "{0}")'.format(libName) )
         if verbosity >= 3:
            print( '  ...completed.' )
      except:
         if verbosity >= 3:
            print( '  ...FAILED!' )
   
   if verbosity >= 1:
      print( )
   
   return listener

@LDefPrimitive( 'parse' )
def LP_parse( env, *args, **keys ):
   inputExprStr = args[0]
   return theListener.parse( inputExprStr )

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


if __name__ == '__main__':
   print( 'Lyps Interpreter' )
   theListener = LypsListener( )
   print( '- Execution environment initialized.' )

   theListener.rebootExecutionEnvironment( STANDARD_LIBRARIES )
   print( '- Runtime library initialized.' )
   
   print( 'Welcome!' )
   print( 'Enter a Lyps expression, or type ]help for listener commands.')
   theListener.readEvalPrintLoop( )
   
   print( '\nGoodbye.\n\n\n' )

