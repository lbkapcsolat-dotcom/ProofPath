import NatIndexedHomologyGate
import Mathlib.Algebra.Category.Grp.Abelian
import Mathlib.Algebra.Homology.ConcreteCategory

namespace HomologyGate

set_option autoImplicit false

open CategoryTheory

universe u

noncomputable section

/--
The standard mathlib chain complex associated to our natural-number indexed
additive chain data. The carrier in degree `n` is `C n`, bundled as an
abelian group, and the only potentially nonzero differential is
`d (n+1) n = K.boundary n`.
-/
def mathlibChainComplex
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) : ChainComplex Ab.{u} Nat where
  X n := AddCommGrpCat.of (C n)
  d i j := by
    by_cases h : j + 1 = i
    · subst i
      exact AddCommGrpCat.ofHom (K.boundary j)
    · exact 0
  shape := by
    intro i j hrel
    dsimp
    by_cases h : j + 1 = i
    · exact (hrel h).elim
    · rfl
  d_comp_d' := by
    intro i j k hij hjk
    change j + 1 = i at hij
    change k + 1 = j at hjk
    subst i
    subst j
    ext x
    simp [K.boundary_sq]

/-- The underlying degree-`n` object is exactly the original carrier. -/
theorem mathlib_chain_X_coe
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) :
    ((mathlibChainComplex K).X n : Type u) = C n := by
  rfl

/-- Mathlib's standard `d_{n+1,n}` acts exactly as our boundary map. -/
theorem mathlib_chain_d_succ_apply
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) (x : C (Nat.succ n)) :
    (mathlibChainComplex K).d (Nat.succ n) n x = K.boundary n x := by
  simp [mathlibChainComplex]

/-- Every differential forbidden by `ComplexShape.down Nat` is zero. -/
theorem mathlib_chain_d_nonrel_eq_zero
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (i j : Nat)
    (h : ¬ (ComplexShape.down Nat).Rel i j) :
    (mathlibChainComplex K).d i j = 0 :=
  (mathlibChainComplex K).shape i j h

/-- The standard consecutive differential composite reduces to our `boundary_sq`. -/
theorem mathlib_chain_d_comp_d_apply
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat)
    (x : C (Nat.succ (Nat.succ n))) :
    (mathlibChainComplex K).d (Nat.succ n) n
      ((mathlibChainComplex K).d (Nat.succ (Nat.succ n)) (Nat.succ n) x) = 0 := by
  rw [mathlib_chain_d_succ_apply K (Nat.succ n), mathlib_chain_d_succ_apply K n]
  exact K.boundary_sq n x

/-- The concrete standard outgoing-cycle equation is our degreewise kernel condition. -/
theorem mathlib_degree_cycle_iff
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) (x : C n) :
    (mathlibChainComplex K).d n (Nat.pred n) x = 0 ↔ NatInKernel K n x := by
  cases n with
  | zero =>
      simp [NatInKernel, natDegreeBoundary, mathlibChainComplex]
  | succ n =>
      change (mathlibChainComplex K).d (Nat.succ n) n x = 0 ↔
        K.boundary n x = 0
      rw [mathlib_chain_d_succ_apply K n]

/-- The concrete standard incoming-boundary equation is our degreewise image condition. -/
theorem mathlib_degree_boundary_iff
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) (x : C n) :
    (∃ y : C (Nat.succ n),
      (mathlibChainComplex K).d (Nat.succ n) n y = x) ↔ NatInImage K n x := by
  constructor
  · rintro ⟨y, hy⟩
    exact ⟨y, by simpa using hy⟩
  · rintro ⟨y, hy⟩
    exact ⟨y, by simpa using hy⟩

end

end HomologyGate
