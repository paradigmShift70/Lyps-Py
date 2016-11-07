from ltk_py3.stackvm import *

'''
fib( arg ):
   if arg <= 2:
      return 1
   else:
      return fib(arg-1) + fib(arg-2)

Sequence:  1   1   2   3   5   8  13  21  34  55
Position:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15
'''

if __name__ == '__main__':
   vm = StackVM3( )
   
   fiby = CodeObject( vm.opcodes, src=[               # [ ..., arg ]
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH',                  2 ],
      [                  'iCMP'                     ],
      [                  'JMP_GT',          'else:' ],
      [                  'PUSH',                  1 ],
      [                  'RET'                      ],
      [ 'else:',         'PUSH_BPOFF',           -1 ],
      [                  'iDEC'                     ],
      [                  'PUSH_CS'                  ],
      [                  'CALL',                  1 ],   # Recursive call
      [                  'PUSH_BPOFF',           -1 ],
      [                  'PUSH',                  2 ],
      [                  'iSUB'                     ],
      [                  'PUSH_CS'                  ],
      [                  'CALL',                  1 ],   # Recursive call
      [                  'iADD'                     ],
      [ 'end:',          'RET'                      ]
   ] )
   fiby.assemble()
   fiby.link()
   fiby.partialize()

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
      [                  'PUSH',                  1 ],
      [                  'JMP',             'end:'  ],
      [ 'else:',         'PUSH_BPOFF',            0 ],
      [                  'PUSH_BPOFF',            0 ],
      [                  'iDEC'                     ],
      [                  'PUSH_CS'                  ],
      [                  'CALL',                  1 ],
      [                  'iMUL'                     ],
      [ 'end:',          'RETY'                     ]
   ]
   fct_exe = assemble( fct )
   
   prog2 = CodeObject( vm.opcodes, src=[
      [                  'PUSH',                  25 ],
      [                  'PUSH', fiby.executableCode ],   # push the function
      [                  'CALL',                   1 ],   # call the function
      [                  'HALT'                      ]
   ] )
   prog2.assemble()
   prog2.link()
   prog2.partialize()
   
   
   from perftesting import PerfTimer
   
   entryPoint = prog2.executableCode
   '''
   for instructionNum,vmState in enumerate(vm.iterrun( entryPoint )):
      vmState._trace( instructionNum, hexintegers=True )
   resultExpr = vm.last
   print(resultExpr)
   
   '''
   intructionCount = 0
   with PerfTimer( ):
      #vm.run( entryPoint )   
      instructionCount = vm.run( entryPoint )

   print( vm.SS.pop() )
   PerfTimer.dump( )
   if instructionCount > 0:
      print( 'Number of vm instructions executed: {:d}.'.format(instructionCount))
   
   
   
   