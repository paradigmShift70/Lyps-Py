from LypsListener import *
from unittest import *

class LypsTest_Arithmetic( LypsTestCase ):
   def test_math( self ):
      self.test( '(+ 10 1)',)
   def test_math_addition_001( self ):
      self.assertExprEqual( '(+ 1 2)',                              '3' )
   def test_math_addition_002( self ):
      self.assertExprEqual( '(+ 9 2 5 6)',                          '22' )
   def test_math_addition_003( self ):
      self.assertExprEqual( '(+ 1/2 1/3)',                          '5/6' )
   def test_math_addition_004( self ):
      self.assertExprEqual( '(+ 2 0.5 1/2)',                        '3.0' )
   def test_math_addition_005( self ):
      self.assertExprEqual( '(+ 4)',                                '4'    )

   def test_math_subtraction_001( self ):
      self.assertExprEqual( '(- 15 8)',                             '7' )
   def test_math_subtraction_002( self ):
      self.assertExprEqual( '(- 10 2 3)',                           '5' )
   def test_math_subtraction_003( self ):
      self.assertExprEqual( '(- 4)',                                '-4'   )

   def test_math_mult_001( self ):
      self.assertExprEqual( '(* 2 3)',                              '6' )
   def test_math_mult_002( self ):
      self.assertExprEqual( '(* 2 5 3 4)',                          '120' )
   def test_math_mult_003( self ):
      self.assertExprEqual( '(* 2 5 3 4)',                          '120' )
   def test_math_mult_004( self ):
      self.assertExprEqual( '(* 1/2 1/3 1/10)',                     '1/60' )

   def test_math_div_001( self ):
      self.assertExprEqual( '(/ 6 2)',                              '3.0'  )
   def test_math_div_002( self ):
      self.assertExprEqual( '(/ 6 0.5)',                            '12.0' )
   def test_math_div_003( self ):
      self.assertExprEqual( '(/ 5 2 7)',             '0.35714285714285715' )
   
   def test_math_log_001( self ):
      self.assertExprEqual( '(log 2.7)',             '0.4313637641589873' )
   def test_math_log_002( self ):
      self.assertExprEqual( '(log 1000 10)',         '2.9999999999999996' )

   def test_math_sin_001( self ):
      self.assertExprEqual( '(sin 1.6)',             '0.9995736030415051' )
   
   def test_math_cos_001( self ):
      self.assertExprEqual( '(cos 3)',               '-0.9899924966004454' )
   
   def test_math_pow_001( self ):
      self.assertExprEqual( '(pow 3 2)',             '9'    )
   def test_math_pow_002( self ):
      self.assertExprEqual( '(pow 2 4)',             '16'   )
   def test_math_pow_003( self ):
      self.assertExprEqual( '(pow 10 3)',            '1000' )
   def test_math_pow_004( self ):
      self.assertExprEqual( '(pow 10 -2)',           '0.01' )
   def test_math_pow_005( self ):
      self.assertExprEqual( '(pow 9 1/2)',           '3.0'  )
   def test_math_pow_006( self ):
      self.assertExprEqual( '(pow 16 1/2)',          '4.0'  )
   def test_math_pow_007( self ):
      self.assertExprEqual( '(pow 1/4 1/2)',         '0.5'  )
   
   def test_math_mod_001( self ):
      self.assertExprEqual( '(mod 3 3)',             '0'    )
   def test_math_mod_002( self ):
      self.assertExprEqual( '(mod 4 3)',             '1'    )
   def test_math_mod_003( self ):
      self.assertExprEqual( '(mod 5 3)',             '2'    )
   def test_math_mod_004( self ):
      self.assertExprEqual( '(mod 6 3)',             '0'    )
   def test_math_mod_005( self ):
      self.assertExprEqual( '(mod 7 3)',             '1'    )
   def test_math_mod_006( self ):
      self.assertExprEqual( '(mod 8 3)',             '2'    )
   def test_math_mod_007( self ):
      self.assertExprEqual( '(mod 9 3)',             '0'    )
   def test_math_mod_008( self ):
      self.assertExprEqual( '(mod 9 4)',             '1'    )
   
   def test_math_float_001( self ):
      self.assertExprEqual( '(float 1/4)',           '0.25' )
   def test_math_float_002( self ):
      self.assertExprEqual( '(float 1/100)',         '0.01' )
   
   def test_math_float_003( self ):
      self.assertExprEqual( '(* 2 1000 1000 1000)',         '2000000000'   )
   def test_math_float_004( self ):
      self.assertExprEqual( '(float (* 2 1000 1000 1000))', '2000000000.0' )
   def test_math_float_005( self ):
      self.assertExprEqual( '(* 2 1/1000 1/1000)',          '1/500000' )
   def test_math_float_006( self ):
      self.assertExprEqual( '(float (* 2 1/1000 1/1000))',  '2e-06' )

TestSuite02 = [
   ( '(write! (+ 1 3))',             '4'     ),
   ( '(+ 2 (write! 7))',             '9'     ),
   ( '(write! (write! (write! (write! 7))))', '7777' )
   ]

TestSuite10 = [
   ("0","0"),
   ("1","1"),
   ('(- 3)', '-3' ),
   ("null", "NULL"),
   ("()", "NULL"),
   ("(+ 1 1)", "2"),
   ("(+ 10 2)", "12"),
   ("(+ 2 10)", "12"),
   ("(+ 3.14 2.71)", "5.85"),
   ("(- 10 2)", "8"),
   ("(* 9 3)","27"),
   ("(/ 27 3)","9.0"),
   ("(+ (* 2 2) (/ 2 2))","5.0"),
   ("(first '(fast computers are nice))","FAST"),
   ("(first '(a b c))","A"),
   ("(rest '(fast computers are nice))", "(COMPUTERS ARE NICE)"),
   ("(rest '(a b c))","(B C)"),
   ("(rest '(c))","()"),
   ("(first '((a b) (c d)))","(A B)"),
   ("(first (rest '(a b c)))","B"),
   ("(first '(rest (a b c)))","REST"),
   ("(set! 'ab-list '(a b))","(A B)"),
   ("ab-list","(A B)"),
   ("'ab-list","AB-LIST"),
   ("(cons 'a '(b c))","(A B C)"),
   ("'(1 a \"hello there\" 3.14 '())", "(1 A \"hello there\" 3.14 (QUOTE ()))"),
   ("(set! 'friends '(dick jane sally))", "(DICK JANE SALLY)"),
   ("(set! 'enemies '(troll grinch ghost))", "(TROLL GRINCH GHOST)"),
   ("(set! 'enemies (remove 'ghost enemies))","(TROLL GRINCH)"),
   ("(set! 'friends (cons 'ghost friends))","(GHOST DICK JANE SALLY)"),
   ("(= 'a 'a)", "1")
   ]

TestSuite99 = [
   #("(set! 'friends '(dick jane sally))", "(DICK JANE SALLY)"),
   ("(set! 'enemies '(troll grinch ghost))", "(TROLL GRINCH GHOST)"),
   ("(remove 'ghost enemies)","(TROLL GRINCH)"),
   ("(set! 'enemies (remove 'ghost enemies))","(TROLL GRINCH)"),
   #("(set! 'friends (cons 'ghost friends))","(GHOST DICK JANE SALLY)")
   ]

