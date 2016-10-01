import Scanner
from Scanner import ParseError, ScannerState
import fractions

class LypsScanner( Scanner.Scanner ):
   WHITESPACE     = ' \t\n\r'
   SIGN           = '+-'
   DIGIT          = '0123456789'
   SIGN_OR_DIGIT  = SIGN + DIGIT
   ALPHA_LOWER    = 'abcdefghijklmnopqrstuvwxyz'
   ALPHA_UPPER    = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
   ALPHA          = ALPHA_LOWER + ALPHA_UPPER
   SYMBOL_OTHER   = '~!@$%^&*_=\/?<>'
   SYMBOL_FIRST   = ALPHA + SIGN + SYMBOL_OTHER
   SYMBOL_REST    = ALPHA + SIGN + SYMBOL_OTHER + DIGIT + ':'

   EOF_TOK            =   0

   SYMBOL_TOK         = 101    # Value Objects
   STRING_TOK         = 102
   INTEGER_TOK        = 111
   FLOAT_TOK          = 112
   FRAC_TOK           = 121

   OPEN_BRACKET_TOK   = 201    # Paired Symbols
   CLOSE_BRACKET_TOK  = 202
   OPEN_PAREN_TOK     = 211
   CLOSE_PAREN_TOK    = 212

   SEMI_COLON_TOK     = 500    # Other Symbols
   POUND_SIGN_TOK     = 501
   PIPE_TOK           = 502
   COLON_TOK          = 503
   SINGLE_QUOTE_TOK   = 504

   def __init__( self, ):
      super( ).__init__( )

   def tokenize( self, aString, EOFToken=0 ):
      try:
         tokenList = super().tokenize( aString, EOFToken )

         for tokLexPair in tokenList:
            print( '{0:<4} /{1}/'.format( *tokLexPair ) )

      except ParseError as ex:
         print( ex.errorString(verbose=True) )

      except Exception as ex:
         print( ex )

   def _scanNextToken( self ):
      buf = self.buffer
      
      try:
         self._skipWhitespaceAndComments( )

         nextChar = buf.peek( )
         if nextChar is None:
            return LypsScanner.EOF_TOK
         if nextChar == '[':
            buf.markStartOfLexeme( )
            buf.consume( )
            return LypsScanner.OPEN_BRACKET_TOK
         elif nextChar == ']':
            buf.markStartOfLexeme( )
            buf.consume( )
            return LypsScanner.CLOSE_BRACKET_TOK
         elif nextChar == '(':
            buf.markStartOfLexeme( )
            buf.consume( )
            return LypsScanner.OPEN_PAREN_TOK
         elif nextChar == ')':
            buf.markStartOfLexeme( )
            buf.consume( )
            return LypsScanner.CLOSE_PAREN_TOK
         elif nextChar == ';':
            buf.markStartOfLexeme( )
            buf.consume( )
            return LypsScanner.SEMI_COLON_TOK
         elif nextChar == '#':
            buf.markStartOfLexeme( )
            buf.consume( )
            return LypsScanner.POUND_SIGN_TOK
         elif nextChar == '|':
            buf.markStartOfLexeme( )
            buf.consume( )
            return LypsScanner.PIPE_TOK
         elif nextChar == ':':
            buf.markStartOfLexeme( )
            buf.consume( )
            nextChar = buf.peek( )
            return LypsScanner.COLON_TOK
         elif nextChar == "'":
            buf.markStartOfLexeme( )
            buf.consume( )
            nextChar = buf.peek( )
            return LypsScanner.SINGLE_QUOTE_TOK
         elif nextChar == '"':
            return self._scanStringLiteral( )
         elif nextChar in LypsScanner.SIGN_OR_DIGIT:
            return self._scanNumOrSymbol( )
         elif nextChar in LypsScanner.SYMBOL_FIRST:
            return self._scanSymbol( )
         else:
            raise ParseError( self, 'Unknown Token' )

      except ParseError:
         raise

      except:
         #print( 'Unknown parsing error, assuming EOF' )
         return LypsScanner.EOF_TOK

   def _scanStringLiteral( self ):
      buf = self.buffer
      
      nextChar = buf.peek( )
      if nextChar != '"':
         raise ParseError( self, '\'"\' expected.' )
      buf.markStartOfLexeme( )
      buf.consume( )
      buf.consumeUpTo( '"' )
      buf.consume( )

      return LypsScanner.STRING_TOK

   def _scanNumOrSymbol( self ):
      buf = self.buffer
      
      SAVE = ScannerState( )
      nextChar = buf.peek( )

      buf.markStartOfLexeme( )
      self.saveState( SAVE )                  # Save the scanner state

      buf.consume( )

      if nextChar in LypsScanner.SIGN:
         secondChar = buf.peek( )
         if (secondChar is None) or (secondChar not in LypsScanner.DIGIT):
            self.restoreState( SAVE )         # Restore the scanner state
            return self._scanSymbol( )

      buf.consumePast( LypsScanner.DIGIT )

      if buf.peek() == '.':
         # Possibly a floating point number
         self.saveState( SAVE )
         buf.consume()
         if buf.peek() not in LypsScanner.DIGIT:
            # Integer
            self.restoreState( SAVE )
         else:
            buf.consumePast( LypsScanner.DIGIT )
         return LypsScanner.FLOAT_TOK
      elif buf.peek() == '/':
         # Possibly a Fraction number
         buf.consume( )

         if nextChar in LypsScanner.SIGN:
            secondChar = buf.peek( )
            if (secondChar is None) or (secondChar not in LypsScanner.DIGIT):
               self.restoreState( SAVE )         # Restore the scanner state
               return self._scanSymbol( )
            buf.consume( )

         buf.consumePast( LypsScanner.DIGIT )
         return LypsScanner.FRAC_TOK

      return LypsScanner.INTEGER_TOK

   def _scanSymbol( self ):
      buf = self.buffer
      
      buf.markStartOfLexeme( )
      nextChar = buf.peek()
      if nextChar not in LypsScanner.SYMBOL_FIRST:
         raise ParseError( self, 'Invalid symbol character' )
      buf.consume( )

      buf.consumePast( LypsScanner.SYMBOL_REST )

      return LypsScanner.SYMBOL_TOK

   def _skipWhitespaceAndComments( self ):
      buf = self.buffer
      
      SAVE = ScannerState( )

      while buf.peek() in '; \t\n\r':
         buf.consumePast( ' \t\n\r' )

         if buf.peek() == ';':
            self.saveState( SAVE )
            buf.consume()
            if buf.peek() == ';':
               buf.consumeUpTo( '\n\r' )
            else:
               self.restoreState( SAVE )
               return


if __name__ == '__main__':
   scn = LypsScanner( )
   scn.tokenize( '(a b c)\n' )
   #scn.tokenize( '(set! mem (map \'( (a 0) (b 1) (c "Hello, World!") (d 3.14) (e null) (f asymbol) )))\n' )
