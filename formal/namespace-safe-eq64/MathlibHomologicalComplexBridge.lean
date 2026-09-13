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
  change (ConcreteCategory.hom ((mathlibChainComplex K).d (Nat.succ n) n)) x =
    K.boundary n x
  rw [hd]
  rfl

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
      have hzero :
          (ConcreteCategory.hom ((mathlibChainComplex K).d 0 0)) x = 0 := by
        calc
          (ConcreteCategory.hom ((mathlibChainComplex K).d 0 0)) x =
              (ConcreteCategory.hom
                (0 : (mathlibChainComplex K).X 0 ⟶ (mathlibChainComplex K).X 0)) x :=
            ConcreteCategory.congr_hom hd x
          _ = 0 := rfl
      constructor
      · intro _
        rfl
      · intro _
        exact hzero
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

/-- For a natural-number chain complex, mathlib's next index is exactly `pred`. -/
private theorem mathlib_chain_next_eq_pred (n : Nat) :
    (ComplexShape.down Nat).next n = Nat.pred n := by
  cases n with
  | zero => exact ChainComplex.next_nat_zero
  | succ n => simpa [Nat.succ_eq_add_one] using ChainComplex.next_nat_succ n

/-- The explicit three-object short complex used to compute degree-`n` homology. -/
private abbrev mathlibDegreeShortComplex
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) : ShortComplex Ab.{u} :=
  (mathlibChainComplex K).sc' (Nat.succ n) n (Nat.pred n)

/-- The explicit additive quotient underlying mathlib's degree-`n` homology. -/
private abbrev mathlibDegreeExplicitHomology
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) :=
  (AddMonoidHom.ker (mathlibDegreeShortComplex K n).g.hom) ⧸
    AddMonoidHom.range (mathlibDegreeShortComplex K n).abToCycles

/-- A custom cycle, viewed as an element of mathlib's explicit kernel. -/
private def mathlibDegreeKernelCycle
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) (x : NatCycle K n) :
    AddMonoidHom.ker (mathlibDegreeShortComplex K n).g.hom := by
  refine ⟨x.1, ?_⟩
  change (ConcreteCategory.hom ((mathlibChainComplex K).d n (Nat.pred n))) x.1 = 0
  exact (mathlib_degree_cycle_iff K n x.1).2 x.2

/--
The quotient map from our setoid presentation to mathlib's explicit
`ker dₙ / range dₙ₊₁` presentation.
-/
private noncomputable def mathlibDegreeExplicitMap
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) :
    NatHomologyQuotient K n → mathlibDegreeExplicitHomology K n :=
  Quotient.lift
    (fun x => QuotientAddGroup.mk' _ (mathlibDegreeKernelCycle K n x))
    (by
      intro x y hxy
      apply (QuotientAddGroup.mk'_eq_mk'
        (AddMonoidHom.range (mathlibDegreeShortComplex K n).abToCycles)).2
      rcases hxy with ⟨b, hb⟩
      let z := (mathlibDegreeShortComplex K n).abToCycles b
      refine ⟨z, ?_, ?_⟩
      · exact ⟨b, rfl⟩
      · apply Subtype.ext
        have hb' : x.1 + K.boundary n b = y.1 := hb.symm
        simpa [z, mathlibDegreeKernelCycle, ShortComplex.abToCycles_apply_coe,
          mathlib_chain_d_succ_apply] using hb')

private theorem mathlibDegreeExplicitMap_surjective
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) :
    Function.Surjective (mathlibDegreeExplicitMap K n) := by
  intro q
  obtain ⟨z, rfl⟩ := QuotientAddGroup.mk'_surjective _ q
  have hz := z.2
  change (ConcreteCategory.hom ((mathlibChainComplex K).d n (Nat.pred n))) z.1 = 0 at hz
  let x : NatCycle K n := ⟨z.1, (mathlib_degree_cycle_iff K n z.1).1 hz⟩
  refine ⟨Quotient.mk (natHomologySetoid K n) x, ?_⟩
  change QuotientAddGroup.mk' _ (mathlibDegreeKernelCycle K n x) =
    QuotientAddGroup.mk' _ z
  apply congrArg (QuotientAddGroup.mk' _)
  apply Subtype.ext
  rfl

private theorem mathlibDegreeExplicitMap_injective
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) :
    Function.Injective (mathlibDegreeExplicitMap K n) := by
  intro q₁ q₂
  refine Quotient.inductionOn₂ q₁ q₂ ?_
  intro x y h
  change QuotientAddGroup.mk' _ (mathlibDegreeKernelCycle K n x) =
    QuotientAddGroup.mk' _ (mathlibDegreeKernelCycle K n y) at h
  rcases (QuotientAddGroup.mk'_eq_mk'
    (AddMonoidHom.range (mathlibDegreeShortComplex K n).abToCycles)).1 h with ⟨z, hz, hxy⟩
  rcases hz with ⟨b, rfl⟩
  apply Quotient.sound
  change NatHomologous K n x y
  refine ⟨b, ?_⟩
  have hval := congrArg (fun t => t.1) hxy
  have hval' : x.1 + K.boundary n b = y.1 := by
    simpa [mathlibDegreeKernelCycle, ShortComplex.abToCycles_apply_coe,
      mathlib_chain_d_succ_apply] using hval
  exact hval'.symm

/-- Mathlib's abstract degree-`n` homology, identified with the explicit quotient. -/
private noncomputable def mathlibDegreeHomologyIsoToExplicit
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) :
    (mathlibChainComplex K).homology n ≅
      AddCommGrpCat.of (mathlibDegreeExplicitHomology K n) :=
  (mathlibChainComplex K).homologyIsoSc'
      (Nat.succ n) n (Nat.pred n)
      (by simpa [Nat.succ_eq_add_one] using ChainComplex.prev Nat n)
      (mathlib_chain_next_eq_pred n) ≪≫
    (mathlibDegreeShortComplex K n).abHomologyIso

/--
Canonical map from the custom degreewise quotient into mathlib's standard
homology object. It factors through mathlib's own explicit kernel/range quotient.
-/
noncomputable def mathlibDegreeHomologyMap
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) :
    NatHomologyQuotient K n → ((mathlibChainComplex K).homology n : Type u) :=
  fun q => (mathlibDegreeHomologyIsoToExplicit K n).inv
    (mathlibDegreeExplicitMap K n q)

/-- Every standard mathlib homology class comes from a custom quotient class. -/
theorem mathlibDegreeHomologyMap_surjective
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) :
    Function.Surjective (mathlibDegreeHomologyMap K n) := by
  intro h
  obtain ⟨q, hq⟩ := mathlibDegreeExplicitMap_surjective K n
    ((mathlibDegreeHomologyIsoToExplicit K n).hom h)
  refine ⟨q, ?_⟩
  change (mathlibDegreeHomologyIsoToExplicit K n).inv
      (mathlibDegreeExplicitMap K n q) = h
  rw [hq]
  simp

/-- Equality of mapped classes is exactly equality in the custom quotient. -/
theorem mathlibDegreeHomologyMap_eq_iff
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat)
    (q₁ q₂ : NatHomologyQuotient K n) :
    mathlibDegreeHomologyMap K n q₁ = mathlibDegreeHomologyMap K n q₂ ↔ q₁ = q₂ := by
  constructor
  · intro h
    apply mathlibDegreeExplicitMap_injective K n
    have h' := congrArg
      (fun z => (mathlibDegreeHomologyIsoToExplicit K n).hom z) h
    simpa [mathlibDegreeHomologyMap] using h'
  · intro h
    exact congrArg (mathlibDegreeHomologyMap K n) h

/-- The custom quotient is equivalent to mathlib's standard degree-`n` homology. -/
noncomputable def mathlibDegreeHomologyEquiv
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) :
    NatHomologyQuotient K n ≃ ((mathlibChainComplex K).homology n : Type u) :=
  Equiv.ofBijective (mathlibDegreeHomologyMap K n)
    ⟨(fun q₁ q₂ h => (mathlibDegreeHomologyMap_eq_iff K n q₁ q₂).1 h),
      mathlibDegreeHomologyMap_surjective K n⟩

end

end HomologyGate
