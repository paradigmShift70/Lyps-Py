import ltk_py3.Listener as Listener
from LypsParser import LypsParser
from Lyps import LDefPrimitive, LEnv, L_ATOM
import io


class LypsInterpreter( object ):
   def __init__( self ):
      self._parser = LypsParser( )
      self._env    = LEnv( )
   
   def reboot( self ):
      self._env = self._env.reInitialize( )

   def eval( self, inputExprStr ):
      inputExpr = self._parser.parse( inputExprStr )
      if isinstance(inputExpr, L_ATOM):
         result = inputExpr
      else:
         result = inputExpr.eval( self._env )
      
      return self._makePrintable( result )
   
   def _makePrintable( self, evaluatedObj ):
      if isinstance( evaluatedObj, str ):
         return '"' + evaluatedObj + '"'
      else:
         return str( evaluatedObj )
   
   def runtimeLibraries( self ):
      return [ 'Lybrary.lyps' ]
   
   def testFileList( self ):
      return [ 'test0001.lyps',
               'test0002.lyps' ]

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

if __name__ == '__main__':
   interp = LypsInterpreter( )
   theListener = Listener.Listener( interp, language='Lyps',
                                            version='0.1',
                                            author='Ronald Provost')
   
   theListener.readEvalPrintLoop( )

