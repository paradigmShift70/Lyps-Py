import threading, queue, datetime

class ConsumerMessage( object ):
   NEXT_SERIAL_NUM = 100
   
   def __init__( self, sender, data ):
      self.time        = datetime.datetime.now().isoformat()
      self.serialNo    = ConsumerMessage.NEXT_SERIAL_NUM
      self.sender      = sender
      self.workReq     = data
      self.result      = None
      self.error       = None
      
      ConsumerMessage.NEXT_SERIAL_NUM += 1

 
class ThreadedConsumer( threading.Thread ):
   def __init__( self, **kwds ):
      super().__init__( **kwds )
      self.setDaemon( 1 )
      self.workRequestQueue = queue.PriorityQueue( )
      self.resultQueue      = queue.Queue( )
      self.start( )
   
   def post( self, sender, msg, priority=3 ):
      message    = ConsumerMessage( sender, data )
      
      self.workRequestQueue.put( ( priority, message), block=False, timeout=None )
      
      return message.serialNo
   
   def peekResult( self ):
      return self.resultQueue.get( False )
   
   def getResult( self ):
      return self.resultQueue.get( False )
   
   def run( self ):
      while true:
         prio, message = self.workRequestQueue.get( )
         
         try:
            self._handleRequest( message )
         except:
            message.error = 'UNKNOWN'
         
         self.resultQueue.put( message )
   
   def _handleRequest( self, msg ):
      '''handle the work request (ConsumerMessage).
      If successful,
         msg.result = the result of the completed work
         msg.error  = False
      else
         msg.result = None
         msg.error  = any error information
      '''
      raise NotImplementedError( )
