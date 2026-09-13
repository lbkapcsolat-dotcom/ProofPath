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

/-- Executable equality in mathlib's explicit `ker/range` quotient relation.
This route uses `ShortComplex.abToCycles` directly and never calls the custom
homology predicate. -/
def mathlibClassEq (a b : Z4) : Bool :=
  representatives.any fun t =>
    decide ((mathlibCycle b).1 =
      (mathlibCycle a).1 + (standardShort.abToCycles t).1)

def mathlibMatrix : List (List Bool) :=
  representatives.map fun a => representatives.map fun b => mathlibClassEq a b

def positiveResult : Bool := decide (customMatrix = mathlibMatrix)

theorem positive_mathlib_matches_expected : mathlibMatrix = expectedMatrix := by
  native_decide

theorem positive_routes_equal : customMatrix = mathlibMatrix := by
  native_decide

end RuntimeBindOracle
