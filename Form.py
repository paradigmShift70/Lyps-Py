"""This module defines all the components needed to construct the tree
representation of a wff.
"""


import copy
from StructuredString import *


class Form( object ):
   """Abstract base class for Form classes."""
   # Standard Methods
   def __eq__( self, other ):
      """Is this expression equal to other?
      Category:      Predicate.
      Returns:       boolean.
      Side Effects:  None.
      Preconditions: None.
      """
      assert isinstance( other, Form )

      raise NotImplementedError

   def __ne__( self, other ):
      """Is this expression not equal to other?
      Category:      Predicate.
      Returns:       boolean.
      Side Effects:  None.
      Preconditions: None.
      """
      assert isinstance( other, Form )

      return not(self == other)

   def __str__( self ):
      """Return a string representation of the wff.
      Category:      Function.
      Returns:       str.
      Side Effects:  None.
      Preconditions: None.
      """
      raise NotImplementedError

   def __repr__( self ):
      """Return a string representation of the wff.
      Category:      Function.
      Returns:       str.
      Side Effects:  None.
      Preconditions: None.
      """
      return str( self )

   # Extension
   def atomList( self, lst=None ):
      """Return a list of all the atomic formulas in the WFF.
      Cateogry:      Pure Function.
      Returns:       (list) A list of atomic formulas.
      Side Effects:  None.
      Preconditions: None.
      """
      assert isinstance( lst, list ) or (lst is None)

      if lst is None:
         lst = [ ]

      return self._buildAtomList( lst )

   def mapTo( self, other, aMapping=None ):
      """Presuming that 'other' is a substitution instance of this Form (self).
      Populate the dictionary (aMapping) whose keys are the Atoms of this Form
      instance and whose values are the WFFs of other which correspond to each
      of these Atoms.
      Category:      Pure Function.
      Returns:       (dictionary) The dictionary will contain all the mappings
                     from this instance to other.  If other is not an instance
                     of this, then the dictionary will be empty.
      Side Effects:  None.
      Preconditions: [AssertionError] other must be an WFF.
                     [AssertionError] map must be a dictionary.
      Implementer Note: Any derived implementation should assert the types of
         the arguments.  Any other kinds of exceptions should be avoided or
         cought to insure that the function remains pure.
      """
      assert isinstance( other, Form )
      assert isinstance( aMapping,   dict ) or ( aMapping is None )

      if aMapping is None:
         aMapping={ }

      return self._mapTo( other, aMapping )

   def structuredString( self ):
      """Return a StructuredString representation of the Form.
      Category:      Pure Function.
      Returns:       (MappedString)
      Side Effects:  None.
      Preconditions: None.
      """
      mappedStrBuilder = StructuredStringBuilder( )

      self._buildStructuredString( mappedStrBuilder )

      return mappedStrBuilder.structuredString( )

   def operatorStructure( self ):
      '''Perform a depth-first traversal of the Form appending the primary
      (operator) to operatorList upon entering each node.
         For Sequent use '|-'
         For FormSet use '{[()]}'
         For AtomicWFF use ''
      '''
      operatorList = [ ]

      self._operatorStructure( operatorList )

      return operatorList

   def subordinates( self ):
      '''Return a list of Forms subordinate to this.
      If this is an operator, the Forms must be guaranteed to be in correct
      operand order.  For any other structured Form the ordering is undefined.
      '''
      return [ ]

   def isAtomic( self ):
      """Is the wff atomic?
      Category:     Predicate.
      Returns:      (bool) True if the WFF is atomic.
      Side Effects: None.
      """
      return False

   def arity( self ):
      """Return the arity of the WFF.
      Category:      Pure Function.
      Returns:       (int) The number of argument in the form.
      Side Effects:  None.
      Preconditions: None.
      """
      return len( self )

   def _operatorStructure( self, operatorList ):
      if isinstance( self, AtomicWFF ):
         operatorList.append( '' )
      else:
         operatorList.append( self.primary() )

      for sub in self.subordinates( ):
         sub._operatorStructure( operatorList )

   # Contract
   def primary( self ):
      """Return the primary symbol for the wff.
      Cateogry:      Pure Function.
      Returns:       (str)
      Side Effects:  None.
      Preconditions: None.
      """
      raise NotImplementedError

   def makeInstance( self, aMapping ):
      """Given a mapping, return an instance of this wff. (complement to mapTo())
      Category:      Pure Function.
      Returns:       (WFF) A new instance of this wff.
      Side Effects:  None.
      Preconditions: [AssertionError] mapping must be a dictionary.
                     [ValueError]     Each atom in this wff must be keys in
                        mapping to some other wff.
      """
      raise NotImplementedError

   def _buildAtomList( self, lst ):
      """Implementation of public method atomList( )."""
      raise NotImplementedError

   def _mapTo( self, other, aMapping ):
      """Implementation of public method mapTo( )."""
      assert isinstance( other, Form )
      assert isinstance( aMapping,   dict )

      raise NotImplementedError

   def _buildStructuredString( self, aMappedStrBuilder ):
      """Implementation for mappedString( )."""
      raise NotImplementedError


class WFF( Form ):
   """Abstract base class for well-formed formulas."""
   # Contract
   def copyWithSubstitutedSubWFF( self, subWFFOfThis, newSubWFF ):
      '''Similar to replacing some substring with another, this function
      creates a copy of this WFF replacing the subWFFOfThis (an instance of
      WFF) with newSubForm (an instance of WFF) in the copy.
      Category:      Function.
      Returns:       (WFF).
      Side Effects:  None.
      Preconditions: None.
      '''
      raise NotImplementedError


class AtomicWFF( WFF ):
   """Implementation of atomic well-formed formulas."""
   # Standard Methods
   def __init__( self, aPropSym ):
      """Initialize a new instance of this class.
      Category:      Mutator.
      Returns:       Nothing.
      Side Effects:  Initialize an instance.
      Preconditions: None.
      """
      assert isinstance( aPropSym, str )

      self._sym    = aPropSym

   def __eq__( self, other ):
      """Implement the equality operation.
      Category:       Predicate
      Returns:        (bool) True if 'other' is equal to self.
      Side Effects:   None.
      Preconditions:  None.
      """
      assert isinstance( self._sym, str )

      return isinstance(other, AtomicWFF) and (self._sym == other._sym)

   def __str__( self ):
      """Implement the str() operation.
      Category:       Pure Function.
      Returns:        (str) A string representation of this instance.
      Side Effects:   None.
      Preconditions:  None.
      """
      assert isinstance( self._sym, str )

      return self._sym

   # Specialization of Form
   def primary( self ):
      return ''

   def _buildAtomList( self, lst ):
      """Implementation of public method atomList( )."""
      assert isinstance( lst,       list )

      assert isinstance( self._sym, str  )

      if self._sym not in lst:
         lst.append( self._sym )

      return lst

   def _mapTo( self, other, aMapping ):
      """Implementation of public method mapTo( )."""
      assert isinstance( other,     WFF  )
      assert isinstance( aMapping,  dict )

      assert isinstance( self._sym, str  )

      if self._sym not in aMapping:
         mapCopy = copy.copy( aMapping )
         mapCopy[ self._sym ] = other
         return mapCopy
      elif aMapping[ self._sym ] == other:
         return aMapping
      else:
         return {}

   def makeInstance( self, aMapping ):
      """Given a mapping, return an instance of this wff.
      Category:      Pure Function.
      Returns:       (WFF) A new instance of this wff.
      Side Effects:  None.
      Preconditions: [AssertionError] mapping must be a dictionary.
                     [ValueError]     Each atom in this wff must be keys in
                        mapping to some other wff.
      """
      assert isinstance( aMapping,       dict )

      assert isinstance( self._sym, str  )

      return copy.deepcopy( aMapping[ self._sym ] )

   # Specialization of WFF
   def __len__( self ):
      """Implementation of public method len( )."""
      assert isinstance( self._sym, str )

      return 0

   def isAtomic( self ):
      """Is the wff atomic?
      Category:     Predicate.
      Returns:      (bool) True if the WFF is atomic.
      Side Effects: None.
      """
      assert isinstance( self._sym, str )

      return True

   def primary( self ):
      """Return the primary symbol for the wff.
      Cateogry:      Pure Function.
      Returns:       (str)
      Side Effects:  None.
      Preconditions: None.
      """
      return self._sym

   def copyWithSubstitutedSubWFF( self, subWFFOfThis, newSubWFF ):
      '''Similar to replacing some substring with another, this function
      creates a copy of this WFF replacing the subWFFOfThis (an instance of
      WFF) with newSubWFF (an instance of WFF) in the copy.
      Category:      Function.
      Returns:       (WFF).
      Side Effects:  None.
      Preconditions: None.
      '''
      assert isinstance( subWFFOfThis, WFF )
      assert isinstance( newSubWFF,    WFF )

      if subWFFOfThis is self:
         return newSubWFF
      else:
         return AtomicWFF( self._sym )

   def _buildStructuredString( self, aMappedStrBuilder ):
      """Implementation for mappedString( )."""
      assert isinstance( aMappedStrBuilder, StructuredStringBuilder )
      assert isinstance( self._sym,         str                     )

      regionName = aMappedStrBuilder.beginRegion( )
      aMappedStrBuilder.setClientData( regionName, self )
      aMappedStrBuilder.appendDominant( regionName, self._sym )
      aMappedStrBuilder.endRegion( regionName )

class StructuredWFF( WFF ):
   """Implementation of structured well-formed formulas."""
   # Standard Methods
   def __init__( self, operator, *operands ):
      """Initialize a new instance of the class.
      Category:      Mutator.
      Returns:       Nothing.
      Side Effects:  Initializes an instance.
      Preconditions: [AssertionError] operator, must be a logical operator.
      """
      assert isinstance( operator, str )

      assert len(operands) > 0

      self._operator     = operator
      self._operands     = list(operands)

   def __eq__( self, other ):
      """Implement the equality operation.
      Category:       Predicate
      Returns:        (bool) True if 'other' is equal to self.
      Side Effects:   None.
      Preconditions:  None.
      """
      assert isinstance( self._operator, str  )
      assert isinstance( self._operands, list ) and (len(self._operands) in (1,2))

      return isinstance( other, StructuredWFF ) and (self._operator == other._operator) and (self._operands == other._operands)

   def __str__( self ):
      """Implement the str() operation.
      Category:       Pure Function.
      Returns:        (str) A string representation of this instance.
      Side Effects:   None.
      Preconditions:  None.
      """
      assert isinstance( self._operator, str  )
      assert isinstance( self._operands, list ) and (len(self._operands) in (1,2))

      if len(self._operands) == 1:
         return '%s%s' % ( self._operator, self._operands[0] )
      else:
         return '(%s %s %s)' % ( self._operands[0], self._operator, self._operands[1] )

   # Specialization of Form
   def _buildAtomList( self, lst ):
      """Implementation of public method atomList( )."""
      assert isinstance( lst,            list )

      assert isinstance( self._operator, str  )
      assert isinstance( self._operands, list ) and (len(self._operands) in (1,2))

      for subWFF in self._operands:
         subWFF._buildAtomList( lst )

      return lst

   def _mapTo( self, other, aMapping ):
      """Implementation of public method mapTo( )."""
      assert isinstance( other,          WFF  )
      assert isinstance( aMapping,            dict )

      assert isinstance( self._operator, str  )
      assert isinstance( self._operands, list ) and (len(self._operands) in (1,2))

      if (not isinstance(other, StructuredWFF)) or (self._operator != other._operator) or (len(self._operands) != len(other._operands)):
         return { }

      if len(self._operands) == 1:
         # Unary Operation
         return self._operands[0]._mapTo( other._operands[0], aMapping )

      else:
         # Binary Operation
         subMap = self._operands[0]._mapTo( other._operands[0], aMapping )
         if subMap != { }:
            return self._operands[1]._mapTo( other._operands[1], subMap )
         else:
            return { }

   def makeInstance( self, aMapping ):
      """Given a mapping, return an instance of this wff.
      Category:      Pure Function.
      Returns:       (WFF) A new instance of this wff.
      Side Effects:  None.
      Preconditions: [AssertionError] mapping must be a dictionary.
                     [ValueError]     Each atom in this wff must be keys in
                        mapping to some other wff.
      """
      assert isinstance( aMapping,            dict )

      assert isinstance( self._operator, str  )
      assert isinstance( self._operands, list ) and (len(self._operands) in (1,2))

      if len(self._operands) == 1:
         return StructuredWFF( self._operator, self._operands[0].makeInstance( aMapping ) )

      else:
         return StructuredWFF( self._operator, self._operands[0].makeInstance( aMapping ),
                                               self._operands[1].makeInstance( aMapping ) )

   # Specialization of WFF
   def __len__( self ):
      """Implementation of public method len( )."""
      assert isinstance( self._operator, str  )
      assert isinstance( self._operands, list ) and (len(self._operands) in (1,2))

      return len( self._operands )

   def primary( self ):
      """Return the primary symbol for the wff.
      Cateogry:      Pure Function.
      Returns:       (str)
      Side Effects:  None.
      Preconditions: None.
      """
      return self._operator

   def subordinates( self ):
      """Return a list of the subordinate wffs.
      Cateogry:      Pure Function.
      Returns:       (list)
      Side Effects:  None.
      Preconditions: None.
      """
      return self._operands

   def copyWithSubstitutedSubWFF( self, subWFFOfThis, newSubWFF ):
      '''Similar to replacing some substring with another, this function
      creates a copy of this WFF replacing the subWFFOfThis (an instance of
      WFF) with newSubWFF (an instance of WFF) in the copy.
      Category:      Function.
      Returns:       (WFF).
      Side Effects:  None.
      Preconditions: None.
      '''
      assert isinstance( subWFFOfThis, WFF )
      assert isinstance( newSubWFF,    WFF )

      if subWFFOfThis is self:
         return newSubWFF
      else:
         theOperator = self._operator
         theOperands = [ ]
         for op in self._operands:
            theOperands.append( op.copyWithSubstitutedSubWFF(subWFFOfThis, newSubWFF) )

         return StructuredWFF( theOperator, *theOperands )

   def _buildStructuredString( self, aMappedStrBuilder ):
      """Implementation for mappedString( )."""
      assert isinstance( aMappedStrBuilder, StructuredStringBuilder )
      assert isinstance( self._operator,    str  )
      assert isinstance( self._operands,    list ) and (len(self._operands) in (1,2))

      regionName = aMappedStrBuilder.beginRegion( )
      aMappedStrBuilder.setClientData( regionName, self )

      if len(self._operands) == 1:
         aMappedStrBuilder.appendDominant( regionName, self._operator )
         self._operands[0]._buildStructuredString( aMappedStrBuilder )
      else:
         aMappedStrBuilder.append( '(' )
         self._operands[0]._buildStructuredString( aMappedStrBuilder )
         aMappedStrBuilder.append( ' ' )
         aMappedStrBuilder.appendDominant( regionName, self._operator )
         aMappedStrBuilder.append( ' ' )
         self._operands[1]._buildStructuredString( aMappedStrBuilder )
         aMappedStrBuilder.append( ')' )

      aMappedStrBuilder.endRegion( regionName )

class FormSet( Form ):
   """Represents a set of forms."""
   # Standard Methods
   def __init__( self, forms = None ):
      """Initialize a new instance of the class.
      Category:      Mutator.
      Returns:       Nothing.
      Side Effects:  Initializes an instance.
      Preconditions: [AssertionError] set must be a list or None.
      """
      assert isinstance( forms, list ) or ( forms is None )

      if forms is None:
         self._set = [ ]
      else:
         self._set = forms

      self._optimizeForMapTo( )

   def _optimizeForMapTo( self ):
      # reorganizes the set of forms, placing the in order from most complex
      # to least complex.  For when checking to see if a form is an instance of self

      # heuristic to estimate the complexity of each form
      # operator structure is a list of operators of a Form constructed through
      # a depth-first search through the form.  Here we sort the forms such
      # that those in the set with least-used operator structures are placed first.
      # 
      opStructBin  = { }
      atomOnlyWFFs = [ ]
      for form in self._set:
         # Convert the operatorStructure list into a string
         opStructString = ' '.join( form.operatorStructure( ) )

         # Bin the forms
         if opStructString in opStructBin:
            opStructBin[ opStructString ].append( form )
         else:
            opStructBin[ opStructString ] = [ form ]

      # Create a second set of bins keyed by the number of forms in each opStructBin
      opStructBinSizes = { }
      largestOpStructBin = 0
      for opStructString, forms in opStructBin.items( ):
         binSize = len(forms)
         largestOpStructBin = max( binSize, largestOpStructBin )

         if binSize in opStructBinSizes:
            opStructBinSizes[ binSize ].append( opStructString )
         else:
            opStructBinSizes[ binSize ] = [ opStructString ]

      # Construct a new set sorted by binSize (smallest to largest)
      sortedForms = [ ]
      for binSize in range( 1, largestOpStructBin + 1 ):
         if binSize in opStructBinSizes:
            for formStructString in opStructBinSizes[ binSize ]:
               formsOfThisKind = opStructBin[ formStructString ]
               sortedForms.extend( formsOfThisKind )

      self._set = sortedForms

   def __eq__( self, other ):
      """Implement the equality operation.
      Category:       Predicate
      Returns:        (bool) True if 'other' is equal to self.
      Side Effects:   None.
      Preconditions:  None.
      """
      assert isinstance( self._set, list )

      if not isinstance( other, WFFSet ):
         return False

      for form in self._set:
         if form not in other:
            return False

      for form in other:
         if form not in self._set:
            return False

   def __str__( self ):
      """Implement the str() operation.
      Category:       Pure Function.
      Returns:        (str) A string representation of this instance.
      Side Effects:   None.
      Preconditions:  None.
      """
      assert isinstance( self._set, list )

      result = ''

      isFirst = True
      for form in self:
         if not isFirst:
            result += ', '

         if isinstance( form, Sequent ):
            result += '(' + str(form) + ')'
         else:
            result += str(form)

         isFirst = False

      return result

   def __deepcopy__( self, memoDict ):
      """Return a deep copy of the wff.
      Category:      Function.
      Returns:       (Form).
      Side Effects:  None.
      Preconditions: None.
      """
      return FormSet( copy.deepcopy(self._set, memoDict) )

   # Specialization of Form
   def primary( self ):
      return '{[()]}'

   def atomList( self, lst=None ):
      """Return a list of all the atomic formulas in the WFF.
      Cateogry:      Pure Function.
      Returns:       (list) A list of atomic formulas.
      Side Effects:  None.
      Preconditions: None.
      """
      assert isinstance( lst,       list ) or ( lst is None )

      assert isinstance( self._set, list )

      if lst is None:
         atomList = [ ]
      else:
         atomList = lst

      for form in self:
         form.atomList( atomList )

      return atomList

   def _mapTo( self, anInstSet, aMap ):
      """Implementation of public method mapTo( )."""
      assert isinstance( anInstSet, FormSet )
      assert isinstance( aMap,      dict    )

      assert isinstance( self._set, list    )

      if len( self ) == len( anInstSet ):
         return FormSet._mapSets( self._set, anInstSet._set, aMap )
      else:
         return { }

   def makeInstance( self, aMap ):
      """Given a mapping, return an instance of this wff.
      Category:      Pure Function.
      Returns:       (WFF) A new instance of this wff.
      Side Effects:  None.
      Preconditions: [AssertionError] mapping must be a dictionary.
                     [ValueError]     Each atom in this wff must be keys in
                        mapping to some other wff.
      """
      assert isinstance( aMap,      dict )

      assert isinstance( self._set, list )

      instSet = FormSet( )

      for prop in self:
         instSet.append( prop.makeInstance( aMap ) )

      return instSet

   # Extension
   def __len__( self ):
      """Implementation of public method len( )."""
      assert isinstance( self._set, list )

      return len( self._set )

   def __getitem__( self, key ):
      """Implementation of rvalue subscript operator."""
      assert isinstance( key,       int  )

      assert isinstance( self._set, list )

      return self._set[ key ]

   def __setitem__( self, key, value ):
      """Implementation of lvalue subscript operator."""
      assert isinstance( key,       int  )
      assert isinstance( value,     Form )

      assert isinstance( self._set, list )

      self._set[ key ] = value

   def __delitem__( self, key ):
      """Implementation of del."""
      assert isinstance( key,       int  )

      assert isinstance( self._set, list )

      del self._set[ key ]

   def __iter__( self ):
      """Implementation of iter( )."""
      assert isinstance( self._set, list )

      return iter( self._set )

   def __contains__( self, member ):
      """Implementation of in."""
      assert isinstance( member,    Form )

      assert isinstance( self._set, list )

      return member in self._set

   def append( self, member ):
      """Append a new object to the end of the set.
      Category:      Mutator.
      Returns:       Nothing.
      Side Effects:  Add 'member' to the end of the set.
      Preconditions: [AssertionError] 'member' must be an instance of Form.
      """
      assert isinstance( member,    Form )

      assert isinstance( self._set, list )

      self._set.append( member )

   @staticmethod
   def _mapSets( l1, l2, aMapping ):
      """Implementation of public method _mapTo( )."""
      assert isinstance( l1,  list )
      assert isinstance( l2,  list )
      assert isinstance( aMapping, dict )

      if len(l1) == 0:
         return aMapping
      else:
         for idx1 in range(len(l1)):
            f1 = l1[idx1]

            for idx2 in range(len(l2)):
               f2 = l2[idx2]

               m_copy = copy.deepcopy( aMapping )
               m_copy = f1.mapTo(f2, m_copy)

               if len( m_copy ) > 0:
                  l1_copy = copy.copy( l1 )
                  l1_copy.pop( idx1 )

                  l2_copy = copy.copy( l2 )
                  l2_copy.pop( idx2 )

                  m_copy = FormSet._mapSets( l1_copy, l2_copy, m_copy )

                  if len( m_copy ) > 0:
                     return m_copy

         return { }

   def _buildStructuredString( self, aMappedStrBuilder ):
      """Implementation for mappedString( )."""
      assert isinstance( aMappedStrBuilder, StructuredStringBuilder )

      assert isinstance( self._set, list )

      regionName = aMappedStrBuilder.beginRegion( )
      aMappedStrBuilder.setClientData( regionName, self )
      aMappedStrBuilder.beginDominantMember( regionName )

      isFirst = True
      for entry in self._set:
         if isFirst:
            isFirst = False
         else:
            aMappedStrBuilder.append( ', ' )

         if isinstance( entry, Sequent ):
            aMappedStrBuilder.append( '(' )
            entry._buildMappedString( aMappedStrBuilder )
            aMappedStrBuilder.append( ')' )
         else:
            entry._buildMappedString( aMappedStrBuilder )

      aMappedStrBuilder.endDominantMember( regionName )
      aMappedStrBuilder.endRegion( regionName )


class BadSequentError( Exception ):
   """The sequent being constructed is invalid."""


class SequentApplicationError( Exception ):
   """Unable to apply the sequent as an inference rule."""


class Sequent( Form ):
   """Represents a set of Propositions and sequents."""
   # Standard Methods
   def __init__( self, premiseFormSet=None, conclusionFormSet=None ):
      """Initialize a new instance of the class.
      Category:      Mutator.
      Returns:       Nothing.
      Side Effects:  Initializes an instance.
      Preconditions: [AssertionError] premises must be a FormSet.
                     [AssertionError] conclusions must be a FormSet.
                     [AssertionError] isNested must be bool.
      """
      assert isinstance( premiseFormSet,    FormSet ) or ( premiseFormSet is None )
      assert isinstance( conclusionFormSet, FormSet ) or ( conclusionFormSet is None )

      if (premiseFormSet is not None) or (conclusionFormSet is not None):
         assert (premiseFormSet is not None) and (conclusionFormSet is not None)

      if premiseFormSet is None:
         self._premiseFormSet = FormSet( )
      else:
         self._premiseFormSet = premiseFormSet

      if conclusionFormSet is None:
         self._conclusionFormSet = FormSet( )
      else:
         self._conclusionFormSet = conclusionFormSet

   def __eq__( self, aSeq ):
      """Implement the equality operation.
      Category:       Predicate
      Returns:        (bool) True if 'other' is equal to self.
      Side Effects:   None.
      Preconditions:  None.
      """
      assert isinstance( aSeq,                    Sequent )

      assert isinstance( self._premiseFormSet,    FormSet )
      assert isinstance( self._conclusionFormSet, FormSet )

      return     self._premiseFormSet == aSet._premiseFormSet       \
             and self._conclusionFormSet == aSet._conclusionFormSet

   def __str__( self ):
      """Implement the str() operation.
      Category:       Pure Function.
      Returns:        (str) A string representation of this instance.
      Side Effects:   None.
      Preconditions:  None.
      """
      assert isinstance( self._premiseFormSet,    FormSet )
      assert isinstance( self._conclusionFormSet, FormSet )

      result = ''

      if (len(self._premiseFormSet) == 0) and (len(self._conclusionFormSet) == 0):
         return result

      if len (self._premiseFormSet) > 0:
         result += str( self._premiseFormSet ) + '  |-  ' + str( self._conclusionFormSet )
      else:
         result += '|-  ' + str( self._conclusionFormSet )

      return result

   # Specialization of Form
   def primary( self ):
      return '|-'

   def atomList( self, lst=None ):
      """Return a list of all the atomic formulas in the WFF.
      Cateogry:      Pure Function.
      Returns:       (list) A list of atomic formulas.
      Side Effects:  None.
      Preconditions: None.
      """
      assert isinstance( lst,                     list    ) or ( lst is None )

      assert isinstance( self._premiseFormSet,    FormSet )
      assert isinstance( self._conclusionFormSet, FormSet )

      if lst is None:
         atomList = [ ]
      else:
         atomList = lst

      premiseAtoms = self._premiseFormSet.atomList( atomList )
      return self._conclusionFormSet.atomList( premiseAtoms )

   def _mapTo( self, anInst, aMapping ):
      """Implementation of public method mapTo( ).
      Since mapTo() is only called on premises and premise sets,
      this is only called when a sequent is a premise (closed hypothetical proof).

      For this reason conclusion form set of the sequent is included in the
      mapTo recursive sequence.
      """
      assert isinstance( self._premiseFormSet,    FormSet )
      assert isinstance( self._conclusionFormSet, FormSet )

      assert isinstance( anInst,                  Sequent )
      assert isinstance( aMapping,                dict    )

      subMap = self.mapPremisesTo( anInst._premiseFormSet, aMapping )

      # Map to the conclusion
      subMap = self._conclusionFormSet.mapTo( anInst._conclusionFormSet, subMap )
      if subMap == { }:
         return { }

      return subMap

   def makeInstance( self, aMapping ):
      """Given a mapping, return an instance of this wff.
      Category:      Pure Function.
      Returns:       (WFF) A new instance of this wff.
      Side Effects:  None.
      Preconditions: [AssertionError] mapping must be a dictionary.
                     [ValueError]     Each atom in this wff must be keys in
                        mapping to some other wff.
      """
      assert isinstance( aMapping,                dict    )

      assert isinstance( self._premiseFormSet,    FormSet )
      assert isinstance( self._conclusionFormSet, FormSet )

      premiseSetInst = self._premiseFormSet.makeInstance( aMapping )
      conclusionSetInst = self._conclusionFormSet.makeInstance( aMapping )
      return Sequent( premiseSetInst, conclusionSetInst )

   def __len__( self ):
      """Implementation of public method len( )."""
      return 2

   # Extension
   def premiseSymbols( self ):
      return self.premiseFormSet.atomList( )

   def conclusionSymbols( self ):
      return self.conclusionFormSet.atomeList( )

   def mapPremisesTo( self, aWFFSet, aMapping=None ):
      """Map the premises of this sequent to aWFFSet.
      Category:       Function.
      Returns:        (dict) A mapping of Atomic WFFs from the premises in this sequent to WFFs in aWFFSet.
      Side Effects:   Modifies map.
      Preconditions:  [AssertionError] aWFFSet must be a FormSet.
                      [AssertionError] map must be a dict.
      """
      assert isinstance( aMapping,              dict    ) or ( aMapping is None )

      assert isinstance( self._premiseFormSet,    FormSet )
      assert isinstance( self._conclusionFormSet, FormSet )

      if aMapping is None:
         aMapping = { }

      return self._premiseFormSet.mapTo( aWFFSet, aMapping )

   def conclusionAdditions( self ):
      """Returns a list of atoms present in the conclusions which do not occur
      in any of the premises.
      Category:       Pure Function.
      Returns:        (list) The set of Atomic WFFs in the conclusion set but not in the premises or empty list.
      Side Effects:   None
      Preconditions:  None.
      """
      assert isinstance( self._premiseFormSet,    FormSet )
      assert isinstance( self._conclusionFormSet, FormSet )

      premiseAtoms    = self._premiseFormSet.atomList( )
      conclusionAtoms = copy.copy( self._conclusionFormSet.atomList( ) )

      for premiseAtom in premiseAtoms:
         if premiseAtom in conclusionAtoms:
            conclusionAtoms.remove( premiseAtom )

      return conclusionAtoms

   def applyTo( self, premises, additionalMappings=None ):
      """Attempt to infer a list of conclusions by first mapping the premises
      of this instance onto 'set', then instatiating the conclusion set using
      those mappings.
      Category:        Pure Function.
      Returns:         (list) The list of conclusions.
                       Empty list if set is not an instance of self._premises.
      Side Effects:    None.
      Preconditions:   [AssertionError] set must be a FormSet.
                       [AssertionError] additionalMappings must be a dict or None.
                       [Exception]      set must be an instance of self._premises.
      """
      assert isinstance( premises,                FormSet )
      assert isinstance( additionalMappings, dict    ) or ( additionalMappings is None )

      assert isinstance( self._premiseFormSet,      FormSet )
      assert isinstance( self._conclusionFormSet,   FormSet )

      mapping = self._premiseFormSet.mapTo( premises, additionalMappings )
      if mapping == {}:
         raise SequentApplicationError

      return self._conclusionFormSet.makeInstance( mapping )

   def _buildStructuredString( self, aMappedStrBuilder ):
      """Implementation for mappedString( )."""
      assert isinstance( aMappedStrBuilder, StructuredStringBuilder )

      assert isinstance( self._premiseFormSet,      FormSet )
      assert isinstance( self._conclusionFormSet,   FormSet )

      regionName = aMappedStrBuilder.beginRegion( )
      aMappedStrBuilder.setClientData( regionName, self )

      if len(self._premiseFormSet) > 0:
         self._premiseFormSet._buildMappedString( aMappedStrBuilder )
         aMappedStrBuilder.append( ' ' )
         aMappedStrBuilder.appendDominant( regionName, '|-' )
         aMappedStrBuilder.append( ' ' )
         self._conclusionFormSet._buildMappedString( aMappedStrBuilder )
      else:
         aMappedStrBuilder.appendDominant( regionName, '|-' )
         aMappedStrBuilder.append( ' ' )
         self._conclusionFormSet._buildMappedString( aMappedStrBuilder )

      aMappedStrBuilder.endRegion( regionName )

   def premiseFormSet( self ):
      """Return the set of premises.  .

      Category:      Pure Function
      Returns:       (FormSet)
      Side Effects:  None.
      Preconditions: None.
      """
      assert isinstance( self._premiseFormSet,    FormSet )
      assert isinstance( self._conclusionFormSet, FormSet )

      return self._premiseFormSet

   def conclusionFormSet( self ):
      """Return the set of conclusions.

      Category:      Pure Function
      Returns:       (FormSet)
      Side Effects:  None.
      Preconditions: None.
      """
      assert isinstance( self._premiseFormSet,    FormSet )
      assert isinstance( self._conclusionFormSet, FormSet )

      return self._conclusionFormSet

   def makeConclusionSetInstance( self, aMapping ):
      """Given a mapping, return a substitution instance of the conclusion FormSet.
      Category:      Pure Function.
      Returns:       (WFF) A new substitution instance of the conclusion FormSet.
      Side Effects:  None.
      Preconditions: [AssertionError] mapping must be a dictionary.
                     [ValueError]     Each atom in this wff must be keys in
                        mapping to some other wff.
      """
      assert isinstance( aMapping,                dict    )

      assert isinstance( self._premiseFormSet,    FormSet )
      assert isinstance( self._conclusionFormSet, FormSet )

      return self._conclusionFormSet.makeInstance( aMapping )


