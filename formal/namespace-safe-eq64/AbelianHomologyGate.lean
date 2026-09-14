import Mathlib.Algebra.Group.Hom.Basic
import Mathlib.Algebra.Group.Int.Defs
import Mathlib.Algebra.Group.Prod

namespace HomologyGate

set_option autoImplicit false

universe u₂ u₁ u₀

/--
A three-term chain-complex window `C₂ → C₁ → C₀` in additive commutative
groups. Boundaries are bundled additive homomorphisms, and the chain condition
is the machine-checkable equation `∂₁ ∘ ∂₂ = 0`.
-/
structure AbelianChainData
    (C₂ : Type u₂) (C₁ : Type u₁) (C₀ : Type u₀)
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀] where
  boundary₂ : C₂ →+ C₁
  boundary₁ : C₁ →+ C₀
  boundary_sq : ∀ x, boundary₁ (boundary₂ x) = 0

/-- Middle-degree kernel. -/
def AbelianInKernel
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) (x : C₁) : Prop :=
  C.boundary₁ x = 0

/-- Middle-degree image. -/
def AbelianInImage
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) (x : C₁) : Prop :=
  ∃ y : C₂, C.boundary₂ y = x

/-- Generic gate 1: consecutive boundaries compose to zero. -/
theorem abelian_boundary_sq_zero
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) (x : C₂) :
    C.boundary₁ (C.boundary₂ x) = 0 :=
  C.boundary_sq x

/-- Generic gate 2a: every boundary is a cycle. -/
theorem abelian_image_subset_kernel
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) (x : C₁)
    (hx : AbelianInImage C x) : AbelianInKernel C x := by
  rcases hx with ⟨y, rfl⟩
  exact C.boundary_sq y

/-- A cycle remains a cycle after adding a boundary. -/
theorem abelian_boundary_shift_preserves_cycle
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) (x : C₁) (b : C₂)
    (hx : AbelianInKernel C x) :
    AbelianInKernel C (x + C.boundary₂ b) := by
  unfold AbelianInKernel at hx ⊢
  rw [map_add, hx, C.boundary_sq, zero_add]

/-- Middle-degree cycles. -/
def AbelianCycle
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) :=
  {x : C₁ // AbelianInKernel C x}

/-- Two middle-degree cycles differ by a boundary. -/
def AbelianHomologous
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀)
    (x y : AbelianCycle C) : Prop :=
  ∃ b : C₂, y.1 = x.1 + C.boundary₂ b

private theorem abelianHomologous_refl
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) (x : AbelianCycle C) :
    AbelianHomologous C x x := by
  refine ⟨0, ?_⟩
  simp

private theorem abelianHomologous_symm
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) {x y : AbelianCycle C}
    (h : AbelianHomologous C x y) : AbelianHomologous C y x := by
  rcases h with ⟨b, hb⟩
  refine ⟨-b, ?_⟩
  rw [hb, map_neg]
  simp [add_assoc]

private theorem abelianHomologous_trans
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) {x y z : AbelianCycle C}
    (hxy : AbelianHomologous C x y) (hyz : AbelianHomologous C y z) :
    AbelianHomologous C x z := by
  rcases hxy with ⟨a, ha⟩
  rcases hyz with ⟨b, hb⟩
  refine ⟨a + b, ?_⟩
  rw [hb, ha, map_add, add_assoc]

/-- Generic gate 2b: the boundary relation is a setoid on cycles. -/
def abelianHomologySetoid
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) : Setoid (AbelianCycle C) where
  r := AbelianHomologous C
  iseqv := {
    refl := abelianHomologous_refl C
    symm := abelianHomologous_symm C
    trans := abelianHomologous_trans C
  }

/-- Machine-defined middle homology `ker ∂₁ / im ∂₂`. -/
abbrev AbelianHomologyQuotient
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) :=
  Quotient (abelianHomologySetoid C)

/-- Homologous cycles represent the same generic homology class. -/
theorem abelian_quotient_eq_of_homologous
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀)
    (x y : AbelianCycle C) (h : AbelianHomologous C x y) :
    Quotient.mk (abelianHomologySetoid C) x =
      Quotient.mk (abelianHomologySetoid C) y :=
  Quotient.sound h

/-- Generic non-triviality predicate at the middle degree. -/
def AbelianGlobalNontrivial
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) : Prop :=
  ∃ x : C₁, AbelianInKernel C x ∧ ¬ AbelianInImage C x

/-! ### Integer acyclic countermodel -/

abbrev IntPair := Int × Int

/-- `∂₂(t) = (t,0)` as an additive homomorphism. -/
def intPairBoundary₂ : Int →+ IntPair where
  toFun t := (t, 0)
  map_zero' := rfl
  map_add' _ _ := rfl

/-- `∂₁(a,b) = b` as an additive homomorphism. -/
def intPairBoundary₁ : IntPair →+ Int where
  toFun x := x.2
  map_zero' := rfl
  map_add' _ _ := rfl

theorem intPair_boundary_sq_zero (x : Int) :
    intPairBoundary₁ (intPairBoundary₂ x) = 0 := by
  rfl

/-- Every middle cycle `(a,0)` is the boundary of `a`. -/
theorem intPair_kernel_subset_image (x : IntPair)
    (hx : intPairBoundary₁ x = 0) :
    ∃ y : Int, intPairBoundary₂ y = x := by
  rcases x with ⟨a, b⟩
  change b = 0 at hx
  subst b
  exact ⟨a, rfl⟩

/-- The integer three-term chain window used as the generic countermodel. -/
def intPairChain : AbelianChainData Int IntPair Int where
  boundary₂ := intPairBoundary₂
  boundary₁ := intPairBoundary₁
  boundary_sq := intPair_boundary_sq_zero

/--
Generic gate 3: even for ordinary additive commutative groups, the local chain
condition does not force non-trivial middle homology. The integer complex
`ℤ → ℤ×ℤ → ℤ`, with `t ↦ (t,0)` and `(a,b) ↦ b`, is acyclic in the middle.
-/
theorem abelian_local_conditions_do_not_force_global_nontriviality :
    (∀ x : Int, intPairBoundary₁ (intPairBoundary₂ x) = 0) ∧
    ¬ AbelianGlobalNontrivial (C₂ := Int) (C₁ := IntPair) (C₀ := Int) intPairChain := by
  constructor
  · exact intPair_boundary_sq_zero
  · intro h
    rcases h with ⟨x, hxKernel, hxNotImage⟩
    apply hxNotImage
    unfold AbelianInKernel at hxKernel
    unfold AbelianInImage
    exact intPair_kernel_subset_image x hxKernel

end HomologyGate
