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
abelian group, and `d (n+1) n = K.boundary n`.
-/
def mathlibChainComplex
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) : ChainComplex Ab.{u} Nat :=
  ChainComplex.of
    (fun n => AddCommGrpCat.of (C n))
    (fun n => AddCommGrpCat.ofHom (K.boundary n))
    (by
      intro n
      ext x
      exact K.boundary_sq n x)

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
  have hd :
      (mathlibChainComplex K).d (Nat.succ n) n =
        AddCommGrpCat.ofHom (K.boundary n) := by
    change ChainComplex.of.d
      (fun n => AddCommGrpCat.of (C n))
      (fun n => AddCommGrpCat.ofHom (K.boundary n))
      (Nat.succ n) n = AddCommGrpCat.ofHom (K.boundary n)
    exact ChainComplex.of_d _ _ n
  exact ConcreteCategory.congr_hom hd x

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
      change (ConcreteCategory.hom ((mathlibChainComplex K).d 0 0)) x = 0 ↔
        natDegreeBoundary K 0 x = 0
      have hd : (mathlibChainComplex K).d 0 0 = 0 :=
        mathlib_chain_d_nonrel_eq_zero K 0 0 (by simp [ComplexShape.down])
      have hdx :
          (ConcreteCategory.hom ((mathlibChainComplex K).d 0 0)) x =
            (ConcreteCategory.hom
              (0 : (mathlibChainComplex K).X 0 ⟶ (mathlibChainComplex K).X 0)) x :=
        ConcreteCategory.congr_hom hd x
      constructor
      · intro _
        rfl
      · intro _
        exact hdx
  | succ n =>
      change (mathlibChainComplex K).d (Nat.succ n) n x = 0 ↔
        K.boundary n x = 0
      rw [mathlib_chain_d_succ_apply K n]
      rfl

/-- The concrete standard incoming-boundary equation is our degreewise image condition. -/
theorem mathlib_degree_boundary_iff
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) (x : C n) :
    (∃ y : C (Nat.succ n),
      (mathlibChainComplex K).d (Nat.succ n) n y = x) ↔ NatInImage K n x := by
  constructor
  · rintro ⟨y, hy⟩
    rw [mathlib_chain_d_succ_apply K n] at hy
    exact ⟨y, hy⟩
  · rintro ⟨y, hy⟩
    refine ⟨y, ?_⟩
    rw [mathlib_chain_d_succ_apply K n]
    exact hy

end

end HomologyGate
