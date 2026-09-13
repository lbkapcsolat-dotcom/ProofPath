import AbelianHomologyGate
import Mathlib.Algebra.Group.PUnit

namespace HomologyGate

set_option autoImplicit false

universe u
universe u₂ u₁ u₀

/--
A natural-number indexed chain complex of additive commutative groups.
`boundary n` is the degree-`n` differential `C n → C (n-1)`, with degree zero
forced to zero and consecutive differentials composing to zero in every degree.
-/
structure NatIndexedChainData
    (C : Nat → Type u) [∀ n, AddCommGroup (C n)] where
  boundary : (n : Nat) → C n →+ C (Nat.pred n)
  boundary_zero : ∀ x : C 0, boundary 0 x = 0
  boundary_sq : ∀ (n : Nat) (x : C n),
    boundary (Nat.pred n) (boundary n x) = 0

/-- Degree-`n` cycles. -/
def NatInKernel
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) (x : C n) : Prop :=
  K.boundary n x = 0

/-- Degree-`n` boundaries, i.e. the image of `d_{n+1}`. -/
def NatInImage
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) (x : C n) : Prop :=
  ∃ y : C (n + 1), K.boundary (n + 1) y = x

/-- Every consecutive pair of differentials composes to zero. -/
theorem nat_boundary_sq_zero
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) (x : C n) :
    K.boundary (Nat.pred n) (K.boundary n x) = 0 :=
  K.boundary_sq n x

/-- Every degreewise boundary is a degreewise cycle. -/
theorem nat_image_subset_kernel
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) (x : C n)
    (hx : NatInImage K n x) : NatInKernel K n x := by
  rcases hx with ⟨y, rfl⟩
  unfold NatInKernel
  simpa using K.boundary_sq (n + 1) y

/-- Adding a degree-`n` boundary preserves the cycle condition. -/
theorem nat_boundary_shift_preserves_cycle
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) (x : C n) (b : C (n + 1))
    (hx : NatInKernel K n x) :
    NatInKernel K n (x + K.boundary (n + 1) b) := by
  unfold NatInKernel at hx ⊢
  rw [map_add, hx]
  have hsq := K.boundary_sq (n + 1) b
  simpa using hsq

/-- Degree-`n` cycles as a subtype. -/
def NatCycle
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) :=
  {x : C n // NatInKernel K n x}

/-- Two degree-`n` cycles are homologous when they differ by a degree-`n` boundary. -/
def NatHomologous
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat)
    (x y : NatCycle K n) : Prop :=
  ∃ b : C (n + 1), y.1 = x.1 + K.boundary (n + 1) b

private theorem natHomologous_refl
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) (x : NatCycle K n) :
    NatHomologous K n x x := by
  refine ⟨0, ?_⟩
  simp

private theorem natHomologous_symm
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) {x y : NatCycle K n}
    (h : NatHomologous K n x y) : NatHomologous K n y x := by
  rcases h with ⟨b, hb⟩
  refine ⟨-b, ?_⟩
  rw [hb, map_neg]
  simp [add_assoc]

private theorem natHomologous_trans
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) {x y z : NatCycle K n}
    (hxy : NatHomologous K n x y) (hyz : NatHomologous K n y z) :
    NatHomologous K n x z := by
  rcases hxy with ⟨a, ha⟩
  rcases hyz with ⟨b, hb⟩
  refine ⟨a + b, ?_⟩
  rw [hb, ha, map_add, add_assoc]

/-- The degreewise boundary relation as a setoid on cycles. -/
def natHomologySetoid
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) : Setoid (NatCycle K n) where
  r := NatHomologous K n
  iseqv := {
    refl := natHomologous_refl K n
    symm := natHomologous_symm K n
    trans := natHomologous_trans K n
  }

/-- Degreewise homology `H_n = ker d_n / im d_{n+1}`. -/
abbrev NatHomologyQuotient
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat) :=
  Quotient (natHomologySetoid K n)

/-- Homologous degreewise cycles define equal homology classes. -/
theorem nat_quotient_eq_of_homologous
    {C : Nat → Type u} [∀ n, AddCommGroup (C n)]
    (K : NatIndexedChainData C) (n : Nat)
    (x y : NatCycle K n) (h : NatHomologous K n x y) :
    Quotient.mk (natHomologySetoid K n) x =
      Quotient.mk (natHomologySetoid K n) y :=
  Quotient.sound h

/-! ### Three-term compatibility -/

/--
Carrier family for embedding `C₂ → C₁ → C₀` into a natural-number indexed
complex. Degrees above two are the trivial additive group `PUnit`.
-/
def ThreeTermCarrier
    (C₂ : Type u₂) (C₁ : Type u₁) (C₀ : Type u₀) :
    Nat → Type (max u₂ u₁ u₀)
  | 0 => C₀
  | 1 => C₁
  | 2 => C₂
  | _ => PUnit

instance threeTermCarrierAddCommGroup
    (C₂ : Type u₂) (C₁ : Type u₁) (C₀ : Type u₀)
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (n : Nat) : AddCommGroup (ThreeTermCarrier C₂ C₁ C₀ n) := by
  rcases n with (_ | _ | _ | n)
  · exact inferInstance
  · exact inferInstance
  · exact inferInstance
  · exact inferInstance

/-- The three-term differential family, extended by zero outside degrees 1 and 2. -/
def threeTermBoundary
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) :
    (n : Nat) → ThreeTermCarrier C₂ C₁ C₀ n →+
      ThreeTermCarrier C₂ C₁ C₀ (Nat.pred n)
  | 0 => 0
  | 1 => A.boundary₁
  | 2 => A.boundary₂
  | _ => 0

/-- Exact natural-number indexed realization of the existing three-term model. -/
def threeTermNatChain
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) :
    NatIndexedChainData (ThreeTermCarrier C₂ C₁ C₀) where
  boundary := threeTermBoundary A
  boundary_zero := by
    intro x
    rfl
  boundary_sq := by
    intro n x
    rcases n with (_ | _ | _ | n)
    · rfl
    · rfl
    · exact A.boundary_sq x
    · rfl

/-- Degree one recovers the original `C₁ → C₀` differential exactly. -/
theorem threeTerm_boundary_one_eq
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) (x : C₁) :
    (threeTermNatChain A).boundary 1 x = A.boundary₁ x := by
  rfl

/-- Degree two recovers the original `C₂ → C₁` differential exactly. -/
theorem threeTerm_boundary_two_eq
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) (x : C₂) :
    (threeTermNatChain A).boundary 2 x = A.boundary₂ x := by
  rfl

/-- Degree-one cycles are exactly the cycles of the original three-term model. -/
theorem threeTerm_degree_one_kernel_iff
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) (x : C₁) :
    NatInKernel (threeTermNatChain A) 1 x ↔ AbelianInKernel A x := by
  rfl

/-- Degree-one boundaries are exactly the boundaries of the original model. -/
theorem threeTerm_degree_one_image_iff
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) (x : C₁) :
    NatInImage (threeTermNatChain A) 1 x ↔ AbelianInImage A x := by
  rfl

/-- Degree-one cycle types are equivalent by the identity on underlying elements. -/
def threeTermDegreeOneCycleEquiv
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) :
    NatCycle (threeTermNatChain A) 1 ≃ AbelianCycle A where
  toFun x := ⟨x.1, (threeTerm_degree_one_kernel_iff A x.1).mp x.2⟩
  invFun x := ⟨x.1, (threeTerm_degree_one_kernel_iff A x.1).mpr x.2⟩
  left_inv x := by
    apply Subtype.ext
    rfl
  right_inv x := by
    apply Subtype.ext
    rfl

/-- The degree-one homology relation is exactly the existing middle-degree relation. -/
theorem threeTerm_degree_one_homologous_iff
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀)
    (x y : NatCycle (threeTermNatChain A) 1) :
    NatHomologous (threeTermNatChain A) 1 x y ↔
      AbelianHomologous A (threeTermDegreeOneCycleEquiv A x)
        (threeTermDegreeOneCycleEquiv A y) := by
  rfl

/--
The degree-one homology quotient of the indexed complex is equivalent to the
existing middle homology quotient of the three-term model.
-/
def threeTermDegreeOneHomologyEquiv
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) :
    NatHomologyQuotient (threeTermNatChain A) 1 ≃ AbelianHomologyQuotient A where
  toFun := Quotient.map (threeTermDegreeOneCycleEquiv A)
    (by
      intro x y h
      exact (threeTerm_degree_one_homologous_iff A x y).mp h)
  invFun := Quotient.map (threeTermDegreeOneCycleEquiv A).symm
    (by
      intro x y h
      exact (threeTerm_degree_one_homologous_iff A
        ((threeTermDegreeOneCycleEquiv A).symm x)
        ((threeTermDegreeOneCycleEquiv A).symm y)).mpr h)
  left_inv := by
    intro q
    refine Quotient.inductionOn q ?_
    intro x
    change Quotient.mk _ ((threeTermDegreeOneCycleEquiv A).symm
      (threeTermDegreeOneCycleEquiv A x)) = Quotient.mk _ x
    rw [Equiv.symm_apply_apply]
  right_inv := by
    intro q
    refine Quotient.inductionOn q ?_
    intro x
    change Quotient.mk _ (threeTermDegreeOneCycleEquiv A
      ((threeTermDegreeOneCycleEquiv A).symm x)) = Quotient.mk _ x
    rw [Equiv.apply_symm_apply]

end HomologyGate
