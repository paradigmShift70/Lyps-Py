from ltk_py3.Scanner import *
from LypsScanner import *
from Lyps import *


'''
The Language
------------
Lexical Elements
   Comments
      Comments extend from ';;' through '\n'.
      All text between and including these two delimiters is ignored.

   Delimiters:
      ';', '#', '(', ')', '|', '[', ']', ';;', '\n'

   Literals
      NumberLiteral:  ('+'|'-')('0' .. '9')+ ( '.' ('0' .. '9')+ | '/' ('0' .. '9')+ )   # Decimal or Fraction
      StringLiteral:  '"' (^('"'))* '"'
      Symbol:         'a..zA..Z+-~!@$%^&*_=\:/?<>'
                      { 'a..zA..Z+-~!@$%^&*_=\:/?<>0..9' }

   Reserved Symbols
         'null', 'true', 'false', 'class', 'name', 'parameters'

Grammar
   Start:
      Object EOF
   
   Object:
      NumberLiteral | StringLiteral | Symbol | List | '#' | '|' | ':' | '[' | ']'

   List:
      '(' [ Object { Object } ] ')'
'''


class LypsParser( object ):
   def __init__( self ):
      self._scanner    = LypsScanner( )

   def parse( self, inputString ):
      self._scanner.reset( inputString )

      syntaxTree = self._parseObject( )

      # EOF
      if self._scanner.peekToken( ) != LypsScanner.EOF_TOK:
         raise ParseError( self._scanner, 'EOF Expected.' )

      self._scanner.consume( )

      return syntaxTree

   def _parseObject( self ):
      nextToken = self._scanner.peekToken( )
      
      if nextToken == LypsScanner.INTEGER_TOK:
         lex = self._scanner.getLexeme( )
         lexVal = int(lex)
         self._scanner.consume( )
      elif nextToken== LypsScanner.FLOAT_TOK:
         lex = self._scanner.getLexeme( )
         lexVal = float(lex)
         self._scanner.consume( )
      elif nextToken== LypsScanner.FRAC_TOK:
         lex = self._scanner.getLexeme( )
         lex_num,lex_denom = lex.split('/')
         lex_num   = int(lex_num)
         lex_denom = int(lex_denom)
         lexVal    = fractions.Fraction(lex_num,lex_denom)
         self._scanner.consume( )
      elif nextToken == LypsScanner.STRING_TOK:
         lex = self._scanner.getLexeme( )
         lexVal = lex[1:-1]
         self._scanner.consume( )
      elif nextToken == LypsScanner.SYMBOL_TOK:
         lex = self._scanner.getLexeme( ).upper( )   # Make symbols case insensative
         lexVal = LSymbol(lex)
         self._scanner.consume( )
      elif nextToken == LypsScanner.OPEN_PAREN_TOK:
         lex = self._parseList( )
         lexVal = lex
      elif nextToken == LypsScanner.SINGLE_QUOTE_TOK:
         lex = self._scanner.getLexeme( )
         self._scanner.consume( )
         subordinate = self._parseObject( )
         lexVal = LList( LSymbol('QUOTE'), subordinate )
      elif nextToken in ( LypsScanner.OPEN_BRACKET_TOK, LypsScanner.CLOSE_BRACKET_TOK,
                          LypsScanner.POUND_SIGN_TOK, LypsScanner.PIPE_TOK, LypsScanner.COLON_TOK ):
         lex = self._scanner.getLexeme( )
         lexVal = lex
         self._scanner.consume( )
      else:
         raise ParseError( self._scanner, 'Object expected.' )

      return lexVal

   def _parseList( self ):
      theList = [ ]
      
      # Open List
      if self._scanner.peekToken( ) != LypsScanner.OPEN_PAREN_TOK:
         raise ParseError( self._scanner, '( expected.' )
      else:
         self._scanner.consume( )

      # List Entries
      while self._scanner.peekToken( ) != LypsScanner.CLOSE_PAREN_TOK:
         theList.append( self._parseObject( ) )
      
      # Close List
      if self._scanner.peekToken( ) != LypsScanner.CLOSE_PAREN_TOK:
         raise ParseError( self._scanner, ') expected.')
      else:
         self._scanner.consume( )
   
      return LList( *theList )

if __name__ == '__main__':
   xy = LypsParser( )

   def test( anExpr ):
      print( '\n>>> ', anExpr )
      expr = xy.parse( anExpr )
      print( expr )

   test( '(one two three)' )
   test( '(one (two three) four)' )
   test( '((one) two)' )

