import MathlibHomologicalComplexBridge
import Mathlib.Data.ZMod.Basic

namespace RuntimeBindOracle

open HomologyGate
open CategoryTheory

abbrev Z4 := ZMod 4

def z4Boundary (n : Nat) : Z4 →+ Z4 :=
  match n with
  | 1 => 2 • AddMonoidHom.id Z4
  | _ => 0

def witnessChain : NatIndexedChainData (fun _ : Nat => Z4) where
  boundary := z4Boundary
  boundary_sq := by
    intro n x
    cases n with
    | zero => simp [z4Boundary]
    | succ n =>
        cases n with
        | zero => simp [z4Boundary]
        | succ n => simp [z4Boundary]

def representatives : List Z4 := [0, 1, 2, 3]

def expectedMatrix : List (List Bool) :=
  [ [true,  false, true,  false]
  , [false, true,  false, true ]
  , [true,  false, true,  false]
  , [false, true,  false, true ]
  ]

def degreeOneCycle (x : Z4) : NatCycle witnessChain 1 :=
  ⟨x, by simp [NatInKernel, natDegreeBoundary, witnessChain, z4Boundary]⟩

/-- Executable finite decision of the custom homology relation at degree 1.
The frozen representative list exhausts `ZMod 4`, so this searches every
possible boundary witness in the exact custom relation. -/
def customClassEq (a b : Z4) : Bool :=
  representatives.any fun t =>
    decide (b = a + witnessChain.boundary 1 t)

def customMatrix : List (List Bool) :=
  representatives.map fun a => representatives.map fun b => customClassEq a b

theorem positive_custom_matches_expected : customMatrix = expectedMatrix := by
  native_decide

/-- Mathlib's degree-one short complex for the frozen witness. -/
private abbrev standardShort : ShortComplex Ab :=
  (mathlibChainComplex witnessChain).sc' 2 1 0

/-- A frozen representative, viewed independently as a mathlib kernel cycle. -/
private def mathlibCycle (x : Z4) : AddMonoidHom.ker standardShort.g.hom := by
  refine ⟨x, ?_⟩
  change (ConcreteCategory.hom ((mathlibChainComplex witnessChain).d 1 0)) x = 0
  rw [mathlib_chain_d_succ_apply witnessChain 0]
  simp [witnessChain, z4Boundary]
  rfl

/-- Executable equality in mathlib's explicit `ker/range` quotient relation.
This route uses `ShortComplex.abToCycles` directly and never calls the custom
homology predicate. The carrier is normalized explicitly back to `ZMod 4`
before decidable equality is invoked. -/
def mathlibClassEq (a b : Z4) : Bool :=
  representatives.any fun t =>
    decide (b = a + (show Z4 from (standardShort.abToCycles t).1))

def mathlibMatrix : List (List Bool) :=
  representatives.map fun a => representatives.map fun b => mathlibClassEq a b

def positiveResult : Bool := decide (customMatrix = mathlibMatrix)

theorem positive_mathlib_matches_expected : mathlibMatrix = expectedMatrix := by
  native_decide

theorem positive_routes_equal : customMatrix = mathlibMatrix := by
  native_decide

/-- Test-only mathlib witness with the incoming degree-one boundary removed. -/
def negativeBoundary (_ : Nat) : Z4 →+ Z4 := 0

def negativeChain : NatIndexedChainData (fun _ : Nat => Z4) where
  boundary := negativeBoundary
  boundary_sq := by
    intro n x
    simp [negativeBoundary]

private abbrev negativeShort : ShortComplex Ab :=
  (mathlibChainComplex negativeChain).sc' 2 1 0

def negativeMathlibClassEq (a b : Z4) : Bool :=
  representatives.any fun t =>
    decide (b = a + (show Z4 from (negativeShort.abToCycles t).1))

def negativeMathlibMatrix : List (List Bool) :=
  representatives.map fun a => representatives.map fun b => negativeMathlibClassEq a b

def negativeResult : Bool := decide (customMatrix = negativeMathlibMatrix)

theorem negative_routes_differ : customMatrix ≠ negativeMathlibMatrix := by
  native_decide

def boolJson : Bool → String
  | true => "true"
  | false => "false"

def rowJson (row : List Bool) : String :=
  "[" ++ String.intercalate "," (row.map boolJson) ++ "]"

def matrixJson (matrix : List (List Bool)) : String :=
  "[" ++ String.intercalate "," (matrix.map rowJson) ++ "]"

def renderOracle (negative : Bool) : String :=
  let mathlibObserved := if negative then negativeMathlibMatrix else mathlibMatrix
  let classEqual : Bool := decide (customMatrix = mathlibObserved)
  "{" ++
    "\"schema\":\"MATHLIB_RUNTIME_ORACLE_V1\"," ++
    "\"witness\":\"ZMOD4_H1_BOUNDARY_TIMES_2\"," ++
    "\"degree\":1," ++
    "\"representatives\":[0,1,2,3]," ++
    "\"custom_class_equality\":" ++ matrixJson customMatrix ++ "," ++
    "\"mathlib_class_equality\":" ++ matrixJson mathlibObserved ++ "," ++
    "\"class_equal\":" ++ boolJson classEqual ++ "," ++
    "\"negative_control\":" ++ boolJson negative ++
  "}"

def cliMain (args : List String) : IO UInt32 := do
  if args = [] then
    IO.println (renderOracle false)
    pure 0
  else if args = ["--negative-control"] then
    IO.println (renderOracle true)
    pure 0
  else
    pure 2

end RuntimeBindOracle

def main (args : List String) : IO UInt32 :=
  RuntimeBindOracle.cliMain args
