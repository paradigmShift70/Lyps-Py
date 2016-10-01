class ScannerState( object ):
   def __init__( self ):
      self.tok               = None
      self.buffer_source     = None
      self.buffer_point      = None
      self.buffer_mark       = None
      self.buffer_lineNum    = None

class ScannerBuffer( object ):
   def __init__( self ):
      '''Initialize a scanner buffer instance.'''
      self._source  = ''   # the string to be analyzed lexically
      self._point   = 0    # the current scanner position
      self._mark    = 0    # the first character of the lexeme currently being scanned
      self._lineNum = 0    # the current line number

   def reset( self, sourceString=None ):
      '''Re-initialize the instance over a new or the current string.'''
      assert isinstance( sourceString, str ) or ( sourceString is None )

      if sourceString is None:
         self._source = ''
      else:
         self._source = sourceString

      self._point    = 0
      self._mark     = 0
      self._lineNum  = 0

   def peek( self ):
      '''Return the next character in the buffer.'''
      try:
         return self._source[ self._point ]        # raises on EOF
      except:
         return None   # Scanned past eof
   
   def consume( self ):
      '''Advance the point by one character in the buffer.'''
      try:
         if self._source[ self._point ] == '\n':   # raises on EOF
            self._lineNum += 1
         self._point += 1
      except:
         pass

   def consumeIf( self, aCharSet ):
      '''Consume the next character if it's in aCharSet.'''
      assert isinstance( aCharSet, str ) and (len(aCharSet) > 0)

      try:
         if self._source[ self._point ] in aCharSet:   # raises on EOF
            self.consume( )
      except:
         pass

   def consumeIfNot( self, aCharSet ):
      '''Consume the next character if it's NOT in aCharSet.'''
      assert isinstance( aCharSet, str ) and (len(aCharSet) > 0)

      try:
         if self._source[ self._point ] not in aCharSet:   # raises on EOF
            self.consume( )
      except:
         pass

   def consumePast( self, aCharSet ):
      '''Consume up to the first character NOT in aCharSet.'''
      assert isinstance( aCharSet, str ) and (len(aCharSet) > 0)

      try:
         while self._source[ self._point ] in aCharSet:   # raises on EOF
            self.consume( )
      except:
         pass

   def consumeUpTo( self, aCharSet ):
      '''Consume up to the first character in aCharSet.'''
      assert isinstance( aCharSet, str ) and (len(aCharSet) > 0)

      try:
         while self._source[ self._point ] not in aCharSet:   # raises on EOF
            self.consume( )
      except:
         pass

   def saveState( self, stateInst ):
      stateInst.buffer_source   = self._source
      stateInst.buffer_point    = self._point
      stateInst.buffer_mark     = self._mark
      stateInst.buffer_lineNum  = self._lineNum

   def restoreState( self, stateInst ):
      self._source   = stateInst.buffer_source
      self._point    = stateInst.buffer_point
      self._mark     = stateInst.buffer_mark
      self._lineNum  = stateInst.buffer_lineNum

   def markStartOfLexeme( self ):
      '''Indicate the start of a lexeme by setting the mark to the current vlaue of point.'''
      self._mark = self._point

   def getLexeme( self ):
      '''Returns the substring spanning from mark to point.'''
      return self._source[ self._mark : self._point ]

   def scanLineNum( self ):
      '''Return a tuple of ( the line num, the column num ) of point.'''
      return self._lineNum + 1

   def scanColNum( self ):
      '''Return a tuple of ( the line num, the column num ) of point.'''
      return self._point - self._linePos( ) + 1

   def scanLineTxt( self ):
      '''Return the complete text of the line currently pointed to by point.'''
      fromIdx = self._linePos( )
      toIdx   = self._source.find( '\n', fromIdx )
      if toIdx == -1:
         return self._source[ fromIdx : ]
      else:
         return self._source[ fromIdx : toIdx ]

   def _linePos( self ):
      '''Return the index into the buffer string of the first character of the current line.'''
      return self._source.rfind( '\n', self._point ) + 1

class Scanner( object ):
   def __init__( self ):
      '''Initialize a Scanner instance.'''
      self.buffer       = ScannerBuffer( )
      self._tok         = -1               # The next token

   def reset( self, sourceString=None ):
      '''Re-initialize the instance over a new or the current string.'''
      assert isinstance( sourceString, str ) or ( sourceString is None )

      self.buffer.reset( sourceString )
      self._tok         = -1
      #self._states      = { }
      self.consume( )

   def peekToken( self ):
      '''Return the next (look ahead) token, but do not consume it.'''
      return self._tok

   def consume( self ):
      '''Advance the scanner to the next token/lexeme in the ScannerBuffer.'''
      self._tok = self._scanNextToken( )

   def getLexeme( self ):
      '''Return the next (look ahead) lexeme, but do not consume it.
      This should be called before consume.'''
      return self.buffer.getLexeme( )

   def saveState( self, stateInst ):
      '''Create a restore point (for backtracking).  The current
      state of the scanner is preserved under aStateName.'''
      stateInst.tok             = self._tok
      self.buffer.saveState( stateInst )

   def restoreState( self, stateInst ):
      '''Restore a saved state (backtrack to the point where the restore point was made).'''
      self._tok = stateInst.tok
      self.buffer.restoreState( stateInst )

   def tokenize( self, aString, EOFToken=0 ):
      tokenList = [ ]

      self.reset( aString )

      while self.peekToken() != EOFToken:
         token = self.peekToken()
         lex   = self.getLexeme( )
         tokenList.append( ( token, lex ) )
         self.consume( )

      tokenList.append( (EOFToken,0) )
      
      return tokenList

   # Contract
   def _scanNextToken( self ):
      """Consume the next token (i.e. scan past it).
      Type:          Mutator - Abstract
      Returns:       Token (actual type determined by implementation, usually an int)
      Preconditions: determined by the implementation.
      Side Effects:  Scans the next token from the source string.
      """
      raise NotImplementedError( )

class ScannerLineStream( object ):
   def __init__( self, inputText ):
      self._lines = inputText.splitlines(keepends=True)
      self._point = 0
   
   def peekLine( self ):
      try:
         return self._lines[ self._point ]
      except:
         raise StopIteration( )
   
   def consumeLine( self ):
      self._point += 1
   
   def currentLineNumber( self ):
      return self._point
   
class ParseError( Exception ):
   def __init__( self, aScanner, errorMessage, filename='' ):
      self.filename   = filename
      self.lineNum    = aScanner.buffer.scanLineNum()
      self.colNum     = aScanner.buffer.scanColNum()
      self.errorMsg   = errorMessage
      self.sourceLine = aScanner.buffer.scanLineTxt()

      self.errInfo = {
         'filename':   self.filename,
         'lineNum':    self.lineNum,
         'colNum':     self.colNum,
         'errorMsg':   self.errorMsg,
         'sourceLine': self.sourceLine
         }

   def generateVerboseErrorString( self ):
      """Generate an error string.
      Category:      Pure Function.
      Returns:       (str) A detailed textual representation of the error.
      Side Effects:  None.
      Preconditions: [AssertionError] The underlying buffer must wrap a string.
      """
      self.errInfo['indentStr'] = ' ' * ( self.errInfo['colNum'] - 1 )
      return 'Syntax Error: {filename}({lineNum},{colNum})\n{sourceLine}\n{indentStr}^ {errorMsg}'.format( **self.errInfo )

