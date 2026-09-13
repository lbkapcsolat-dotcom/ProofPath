import Mathlib.Algebra.Group.Prod

namespace HomologyGate

set_option autoImplicit false

/--
A minimal characteristic-two chain datum. The algebraic laws are stated
explicitly so this unit does not depend on mathlib. `add_cancel_middle` is the
characteristic-two cancellation law `(x+y)+(y+z)=x+z`.
-/
structure F2ChainData where
  Carrier : Type
  zero : Carrier
  add : Carrier → Carrier → Carrier
  add_comm : ∀ x y, add x y = add y x
  add_zero : ∀ x, add x zero = x
  zero_add : ∀ x, add zero x = x
  self_add : ∀ x, add x x = zero
  add_cancel_middle : ∀ x y z, add (add x y) (add y z) = add x z
  boundary : Carrier → Carrier
  boundary_zero : boundary zero = zero
  boundary_add : ∀ x y, boundary (add x y) = add (boundary x) (boundary y)
  boundary_sq : ∀ x, boundary (boundary x) = zero

/-- A cycle is an element killed by the boundary. -/
def InKernel (C : F2ChainData) (x : C.Carrier) : Prop :=
  C.boundary x = C.zero

/-- A boundary is an element in the image of the boundary map. -/
def InImage (C : F2ChainData) (x : C.Carrier) : Prop :=
  ∃ y : C.Carrier, C.boundary y = x

/-- Gate 1: the differential squares to zero. -/
theorem boundary_sq_zero (C : F2ChainData) (x : C.Carrier) :
    C.boundary (C.boundary x) = C.zero :=
  C.boundary_sq x

/-- Gate 2a: `∂² = 0` forces every boundary to be a cycle. -/
theorem image_subset_kernel_of_sq_zero
    (C : F2ChainData) (x : C.Carrier) (hx : InImage C x) :
    InKernel C x := by
  rcases hx with ⟨y, rfl⟩
  exact C.boundary_sq y

/-- Adding a boundary to a cycle stays inside the cycle space. -/
theorem boundary_shift_preserves_cycle
    (C : F2ChainData) (x b : C.Carrier) (hx : InKernel C x) :
    InKernel C (C.add x (C.boundary b)) := by
  unfold InKernel at hx ⊢
  rw [C.boundary_add, hx, C.boundary_sq, C.zero_add]

/-- The subtype of cycles. -/
def Cycle (C : F2ChainData) :=
  {x : C.Carrier // InKernel C x}

/-- Two cycles are homologous when their characteristic-two difference is a boundary. -/
def Homologous (C : F2ChainData) (x y : Cycle C) : Prop :=
  ∃ b : C.Carrier, C.add x.1 y.1 = C.boundary b

private theorem homologous_refl (C : F2ChainData) (x : Cycle C) :
    Homologous C x x := by
  refine ⟨C.zero, ?_⟩
  rw [C.self_add, C.boundary_zero]

private theorem homologous_symm (C : F2ChainData) {x y : Cycle C}
    (h : Homologous C x y) : Homologous C y x := by
  rcases h with ⟨b, hb⟩
  refine ⟨b, ?_⟩
  rw [C.add_comm]
  exact hb

private theorem homologous_trans (C : F2ChainData) {x y z : Cycle C}
    (hxy : Homologous C x y) (hyz : Homologous C y z) :
    Homologous C x z := by
  rcases hxy with ⟨a, ha⟩
  rcases hyz with ⟨b, hb⟩
  refine ⟨C.add a b, ?_⟩
  calc
    C.add x.1 z.1 = C.add (C.add x.1 y.1) (C.add y.1 z.1) :=
      (C.add_cancel_middle x.1 y.1 z.1).symm
    _ = C.add (C.boundary a) (C.boundary b) := by rw [ha, hb]
    _ = C.boundary (C.add a b) := (C.boundary_add a b).symm

/--
Gate 2b: the boundary relation on cycles is an equivalence relation, so the
homology quotient is a genuine Lean `Quotient`, not informal notation.
-/
def homologySetoid (C : F2ChainData) : Setoid (Cycle C) where
  r := Homologous C
  iseqv := {
    refl := homologous_refl C
    symm := homologous_symm C
    trans := homologous_trans C
  }

/-- The machine-defined quotient `ker ∂ / im ∂`. -/
abbrev HomologyQuotient (C : F2ChainData) :=
  Quotient (homologySetoid C)

/-- Homologous cycles map to the same quotient class. -/
theorem quotient_eq_of_homologous
    (C : F2ChainData) (x y : Cycle C) (h : Homologous C x y) :
    Quotient.mk (homologySetoid C) x = Quotient.mk (homologySetoid C) y :=
  Quotient.sound h

/-! ### Tiny acyclic countermodel -/

abbrev TinyCarrier := Bool × Bool

def tinyZero : TinyCarrier := (false, false)

/-- `∂(a,b) = (b,0)`. -/
def tinyBoundary (x : TinyCarrier) : TinyCarrier :=
  (x.2, false)

theorem tiny_boundary_sq_zero (x : TinyCarrier) :
    tinyBoundary (tinyBoundary x) = tinyZero := by
  rcases x with ⟨a, b⟩
  rfl

theorem tiny_kernel_subset_image (x : TinyCarrier)
    (hx : tinyBoundary x = tinyZero) :
    ∃ y : TinyCarrier, tinyBoundary y = x := by
  rcases x with ⟨a, b⟩
  cases b with
  | false =>
      exact ⟨(false, a), rfl⟩
  | true =>
      cases hx

/-- Non-trivial homology means: some cycle is not a boundary. -/
def GlobalNontrivial
    (Carrier : Type) (zero : Carrier) (boundary : Carrier → Carrier) : Prop :=
  ∃ x : Carrier, boundary x = zero ∧ ¬ ∃ y : Carrier, boundary y = x

/--
Gate 3: local square-zero structure does not imply global non-triviality.
The two-bit differential `(a,b) ↦ (b,0)` has `∂²=0` and `ker ∂ = im ∂`, hence
its homology is trivial. This is a countermodel, not a global theorem.
-/
theorem local_conditions_do_not_force_global_nontriviality :
    (∀ x : TinyCarrier, tinyBoundary (tinyBoundary x) = tinyZero) ∧
    ¬ GlobalNontrivial TinyCarrier tinyZero tinyBoundary := by
  constructor
  · exact tiny_boundary_sq_zero
  · intro h
    rcases h with ⟨x, hxKernel, hxNotImage⟩
    exact hxNotImage (tiny_kernel_subset_image x hxKernel)

/-! ### General three-term abelian chain-complex lift -/

universe u₂ u₁ u₀

/--
A three-term chain-complex window `C₂ → C₁ → C₀` in additive commutative
groups. This is the minimal general algebraic interface needed to define the
middle homology `ker ∂₁ / im ∂₂` without assuming characteristic two.
-/
structure AbelianChainData
    (C₂ : Type u₂) (C₁ : Type u₁) (C₀ : Type u₀)
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀] where
  boundary₂ : C₂ → C₁
  boundary₁ : C₁ → C₀
  boundary₂_zero : boundary₂ 0 = 0
  boundary₂_add : ∀ x y, boundary₂ (x + y) = boundary₂ x + boundary₂ y
  boundary₂_neg : ∀ x, boundary₂ (-x) = -(boundary₂ x)
  boundary₁_zero : boundary₁ 0 = 0
  boundary₁_add : ∀ x y, boundary₁ (x + y) = boundary₁ x + boundary₁ y
  boundary₁_neg : ∀ x, boundary₁ (-x) = -(boundary₁ x)
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
  rw [C.boundary₁_add, hx, C.boundary_sq, zero_add]

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
  rw [C.boundary₂_zero, add_zero]

private theorem abelianHomologous_symm
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (C : AbelianChainData C₂ C₁ C₀) {x y : AbelianCycle C}
    (h : AbelianHomologous C x y) : AbelianHomologous C y x := by
  rcases h with ⟨b, hb⟩
  refine ⟨-b, ?_⟩
  rw [hb, C.boundary₂_neg]
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
  calc
    z.1 = y.1 + C.boundary₂ b := hb
    _ = (x.1 + C.boundary₂ a) + C.boundary₂ b := by rw [ha]
    _ = x.1 + (C.boundary₂ a + C.boundary₂ b) := by rw [add_assoc]
    _ = x.1 + C.boundary₂ (a + b) := by rw [C.boundary₂_add]

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

/-- `∂₂(t) = (t,0)`. -/
def intPairBoundary₂ (t : Int) : IntPair :=
  (t, 0)

/-- `∂₁(a,b) = b`. -/
def intPairBoundary₁ (x : IntPair) : Int :=
  x.2

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
  boundary₂_zero := by rfl
  boundary₂_add := by
    intro x y
    simp [intPairBoundary₂]
  boundary₂_neg := by
    intro x
    simp [intPairBoundary₂]
  boundary₁_zero := by rfl
  boundary₁_add := by
    intro x y
    rcases x with ⟨a, b⟩
    rcases y with ⟨c, d⟩
    rfl
  boundary₁_neg := by
    intro x
    rcases x with ⟨a, b⟩
    rfl
  boundary_sq := intPair_boundary_sq_zero

/--
Generic gate 3: even for ordinary additive commutative groups, the local chain
condition does not force non-trivial middle homology. The integer complex
`ℤ → ℤ×ℤ → ℤ`, with `t ↦ (t,0)` and `(a,b) ↦ b`, is acyclic in the middle.
-/
theorem abelian_local_conditions_do_not_force_global_nontriviality :
    (∀ x : Int, intPairBoundary₁ (intPairBoundary₂ x) = 0) ∧
    ¬ AbelianGlobalNontrivial intPairChain := by
  constructor
  · exact intPair_boundary_sq_zero
  · intro h
    rcases h with ⟨x, hxKernel, hxNotImage⟩
    apply hxNotImage
    unfold AbelianInKernel at hxKernel
    unfold AbelianInImage
    exact intPair_kernel_subset_image x hxKernel

end HomologyGate
