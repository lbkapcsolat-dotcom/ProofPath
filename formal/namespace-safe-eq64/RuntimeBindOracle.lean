import MathlibHomologicalComplexBridge
import Mathlib.Data.ZMod.Basic

namespace RuntimeBindOracle

open HomologyGate

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

def customClassEq (a b : Z4) : Bool :=
  decide (NatHomologous witnessChain 1 (degreeOneCycle a) (degreeOneCycle b))

def customMatrix : List (List Bool) :=
  representatives.map fun a => representatives.map fun b => customClassEq a b

theorem positive_custom_matches_expected : customMatrix = expectedMatrix := by
  native_decide

end RuntimeBindOracle
