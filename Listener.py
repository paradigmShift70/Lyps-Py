from Scanner import ParseError
import traceback
import sys
import datetime


class EvaluationError( Exception ):
   def __init__( self, errorMessage ):
      super().__init__( self, errorMessage )


class Listener( object ):
   def __init__( self ):
      super().__init__()

      self._listenerCommandSet = {
         'log':      ( '<filename>',   'Begin logging.',                          self.execLogListenerCommand   ),
         'readLog':  ( '<filename>',   'Read and execute a log file.',            self.execReadLogListenerCommand ),
         'continue': ( '<filename>',   'Continue a prior logging seesion.',       self.execContinueListenerCommand ),
         'close':    ( '',             'Stop logging.',                           self.execCloseListenerCommand ),
         'reset':    ( '',             'Reset the Lyps environment.',             self.execResetListenerCommand ),
         'dump':     ( '',             'Dump the trace of the last error.',       self.execExceptionDumpCommand ),
         'test':     ( '[<filename>]', 'Run ALL/specific Lyps integratity test.', self.execRunTestFileCommand   ),
         'exit':     ( '',             'Exit Lyps listener.',                     self.execExitListenerCommand  ),
         'help':     ( '',             'Display this help.',                      self.execHelpListenerCommand  )
         }

      self._logFile = None
      self._exceptInfo = None

   def writeLn( self, value='' ):
      print( value )
      if self._logFile:
         self._logFile.write( value + '\n' )

   def prompt( self, prompt='' ):
      inputStr = input( prompt )
      if self._logFile:
         self._logFile.write( prompt + inputStr + '\n' )
      return inputStr.strip( )

   def execLogListenerCommand( self, cmdParts ):
      if len(cmdParts) != 2:
         self.writeLn( 'Use:  log <filename>, to begin a new logging session.\n' )
         return

      cmd, filename = cmdParts
      if self._logFile is not None:
         self.writeLn( 'Already logging.\n' )
         return

      self._logFile = open( filename, 'w' )
      if self._logFile is None:
         self.writeLn( 'Unable to open file for writing.' )

      self.writeLn( ';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;' )
      self.writeLn( ';;;;;;  Starting Log ( {0} ): {1}\n'.format( datetime.datetime.now().isoformat(), filename ) )

   def execReadLogListenerCommand( self, cmdParts ):
      if len(cmdParts) != 2:
         self.writeLn( 'Use:  read <filename>, to read a past log file in.\n' )
         return
      
      cmd, filename = cmdParts
      self.readAndEvalFile( filename, testFile=False )
      self.writeLn( 'Log file read successfully: ' + filename )

   def execRunTestFileCommand( self, cmdParts ):
      numArgs = len(cmdParts) - 1
      if numArgs > 1:
         self.writeLn( 'Use:  test [<filename>], to rerun all or a specific test file.\n' )
         return
      
      if numArgs == 1:
         cmd, filename = cmdParts
         filenameList = [ ]
      else:
         filenameList = self._getTestfileList( )
      
      for filename in filenameList:
         self.readAndEvalFile( filename, testFile=True )

   def execContinueListenerCommand( self, cmdParts ):
      if len(cmdParts) != 2:
         self.writeLn( 'Use:  continue <filename>, to begin a new logging session.\n' )
         return

      cmd, filename = cmdParts
      if self._logFile is not None:
         self.writeLn( 'Already logging.\n' )
         return
      
      self.execReadLogListenerCommand( cmdParts )
      
      self._logFile = open( filename, 'a' )
      if self._logFile is None:
         self.writeLn( 'Unable to open file for append.' )
         return
      
      self.writeLn( ';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;' )
      self.writeLn( ';;;;;;  Continuing Log ( {0} ): {1}\n'.format( datetime.datetime.now().isoformat(), filename ) )

   def execCloseListenerCommand( self, cmdParts ):
      self.writeLn( ';;;;;;  Logging ended.' )
      self.writeLn( ';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;' )
      if self._logFile is not None:
         self._logFile.close( )
      
      self._logFile = None

   def execExceptionDumpCommand( self, cmdParts ):
      if self._exceptInfo is None:
         self.writeLn( 'No exception information available.\n' )
      
      sys.excepthook( *self._exceptInfo )

   def execExitListenerCommand( self, cmdParts ):
      self.writeLn( 'Bye.' )
      raise Exception( )

   def execHelpListenerCommand( self, cmdParts ):
      for cmd, parts in self._listenerCommandSet.items():
         args, comments, fn = parts         
         usage = cmd + (' ' + args if len(args) > 0 else '')
         self.writeLn( '{0:<20} {1}'.format( usage, comments ) )
      self.writeLn()

   def execListenerCommand( self, listenerCommand ):
      cmdParts = listenerCommand[1:].split( ' ' )
      cmdParts = [ x for x in cmdParts if x != '' ]
      try:
         commandHandler = self._listenerCommandSet[ cmdParts[0] ][ 2 ]
      except:
         self.writeLn( 'Unknown listener command {0}.\n'.format( cmdParts[0] ) )
         return

      commandHandler( cmdParts )
      self.writeLn( )

   def execResetListenerCommand( self, cmdParts ):
      raise NotImplemented( )

   def readEvalPrintLoop( self ):
      inputExprStr = ''

      while True:
         if inputExprStr == '':
            lineInput = self.prompt( '>>> ' )
         else:
            lineInput = self.prompt( '... ' )

         if (lineInput == '') and (inputExprStr != ''):
            if inputExprStr[0] == ']':
               self.execListenerCommand( inputExprStr[:-1] )
            else:
               try:
                  resultExpr = self._parseAndEvalExpr( inputExprStr )
                  self.writeLn( '\n==> ' + self._printable(resultExpr) )

               except ParseError as ex:
                  self._exceptInfo = sys.exc_info( )
                  self.writeLn( ex.generateVerboseErrorString() )

               except EvaluationError as ex:
                  self._exceptInfo = sys.exc_info( )
                  self.writeLn( ex.args[-1] )

               except Exception as ex:
                  self._exceptInfo = sys.exc_info( )
                  self.writeLn( ex.args[-1] )

               self.writeLn( )
            
            inputExprStr = ''
            
         else:
            inputExprStr += (lineInput.strip() + '\n')

   def readAndEvalFile( self, filename, testFile=False ):
      raise NotImplemented( )

   def parseAndEvalExpr( self, inputExprStr ):
      'Parse and evaluate a lisp expression. Handle exceptions.'
      raise NotImplemented( )

   def _parseAndEvalExpr( self, inputExprStr ):
      'Parse and evaluate a lisp expression.'
      raise NotImplemented( )

   def _getTestfileList( self ):
      raise NotImplemented( )

   def _printable( self, expression ):
      raise NotImplementedError( )

   
