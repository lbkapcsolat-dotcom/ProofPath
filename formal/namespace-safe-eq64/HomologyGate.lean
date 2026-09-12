import Std

namespace HomologyGate

set_option autoImplicit false

/--
A minimal characteristic-two chain datum.  The algebraic laws are stated
explicitly so this unit does not depend on mathlib.  `add_cancel_middle` is the
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
its homology is trivial.  This is a countermodel, not a global theorem.
-/
theorem local_conditions_do_not_force_global_nontriviality :
    (∀ x : TinyCarrier, tinyBoundary (tinyBoundary x) = tinyZero) ∧
    ¬ GlobalNontrivial TinyCarrier tinyZero tinyBoundary := by
  constructor
  · exact tiny_boundary_sq_zero
  · intro h
    rcases h with ⟨x, hxKernel, hxNotImage⟩
    exact hxNotImage (tiny_kernel_subset_image x hxKernel)

end HomologyGate
