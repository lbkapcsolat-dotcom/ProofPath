import NatIndexedHomologyGate
import Mathlib.Algebra.Group.ULift

namespace HomologyGate

set_option autoImplicit false

universe u₂ u₁ u₀ ua ub w

/-- Lift an additive homomorphism across universe levels. -/
private def uliftAddHom
    {α : Type ua} {β : Type ub}
    [AddCommGroup α] [AddCommGroup β]
    (f : α →+ β) : ULift.{w} α →+ ULift.{w} β where
  toFun x := ULift.up (f x.down)
  map_zero' := by
    apply (Equiv.ulift).injective
    simp
  map_add' := by
    intro x y
    apply (Equiv.ulift).injective
    simp

/--
Lift all three carriers of an arbitrary-universe chain window into one common
universe before reusing the already-proved same-universe three-term embedding.
-/
private def uliftedAbelianChainData
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) :
    AbelianChainData
      (ULift.{max u₂ (max u₁ u₀)} C₂)
      (ULift.{max u₂ (max u₁ u₀)} C₁)
      (ULift.{max u₂ (max u₁ u₀)} C₀) where
  boundary₂ := uliftAddHom A.boundary₂
  boundary₁ := uliftAddHom A.boundary₁
  boundary_sq := by
    intro x
    apply (Equiv.ulift).injective
    simp [uliftAddHom, A.boundary_sq]

/-- Common-universe carrier obtained by lifting the original three carriers. -/
abbrev ULiftedThreeTermCarrier
    (C₂ : Type u₂) (C₁ : Type u₁) (C₀ : Type u₀) :
    Nat → Type (max u₂ (max u₁ u₀)) :=
  ThreeTermCarrier
    (ULift.{max u₂ (max u₁ u₀)} C₂)
    (ULift.{max u₂ (max u₁ u₀)} C₁)
    (ULift.{max u₂ (max u₁ u₀)} C₀)

/--
The arbitrary-universe three-term model embedded into the indexed complex by
first lifting its three carriers and then reusing `threeTermNatChain`.
-/
def uliftedThreeTermNatChain
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) :
    NatIndexedChainData (ULiftedThreeTermCarrier C₂ C₁ C₀) :=
  threeTermNatChain (uliftedAbelianChainData A)

/-- Lowering the lifted degree-one differential recovers `boundary₁`. -/
theorem uliftedThreeTerm_boundary_one_down_eq
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀)
    (x : ULiftedThreeTermCarrier C₂ C₁ C₀ 1) :
    (natDegreeBoundary (uliftedThreeTermNatChain A) 1 x).down =
      A.boundary₁ x.down := by
  have h := threeTerm_boundary_one_eq (uliftedAbelianChainData A) x
  have hd := congrArg ULift.down h
  simpa [uliftedThreeTermNatChain, uliftedAbelianChainData, uliftAddHom] using hd

/-- Lowering the lifted degree-two differential recovers `boundary₂`. -/
theorem uliftedThreeTerm_boundary_two_down_eq
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀)
    (x : ULiftedThreeTermCarrier C₂ C₁ C₀ 2) :
    (natDegreeBoundary (uliftedThreeTermNatChain A) 2 x).down =
      A.boundary₂ x.down := by
  have h := threeTerm_boundary_two_eq (uliftedAbelianChainData A) x
  have hd := congrArg ULift.down h
  simpa [uliftedThreeTermNatChain, uliftedAbelianChainData, uliftAddHom] using hd

/-- Lifted degree-one cycles are exactly original middle-degree cycles. -/
theorem uliftedThreeTerm_degree_one_kernel_iff
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀)
    (x : ULiftedThreeTermCarrier C₂ C₁ C₀ 1) :
    NatInKernel (uliftedThreeTermNatChain A) 1 x ↔
      AbelianInKernel A x.down := by
  unfold NatInKernel AbelianInKernel
  constructor
  · intro h
    have hd := congrArg ULift.down h
    rw [uliftedThreeTerm_boundary_one_down_eq A x] at hd
    simpa using hd
  · intro h
    apply (Equiv.ulift).injective
    rw [uliftedThreeTerm_boundary_one_down_eq A x]
    simpa using h

/-- Lifted degree-one boundaries are exactly original middle-degree boundaries. -/
theorem uliftedThreeTerm_degree_one_image_iff
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀)
    (x : ULiftedThreeTermCarrier C₂ C₁ C₀ 1) :
    NatInImage (uliftedThreeTermNatChain A) 1 x ↔
      AbelianInImage A x.down := by
  unfold NatInImage AbelianInImage
  constructor
  · rintro ⟨y, hy⟩
    refine ⟨y.down, ?_⟩
    change natDegreeBoundary (uliftedThreeTermNatChain A) 2 y = x at hy
    have hd := congrArg ULift.down hy
    rw [uliftedThreeTerm_boundary_two_down_eq A y] at hd
    simpa using hd
  · rintro ⟨y, hy⟩
    refine ⟨ULift.up y, ?_⟩
    change natDegreeBoundary (uliftedThreeTermNatChain A) 2 (ULift.up y) = x
    apply (Equiv.ulift).injective
    rw [uliftedThreeTerm_boundary_two_down_eq A (ULift.up y)]
    simpa using hy

/-- Degree-one lifted cycles are equivalent to the original middle cycles. -/
def uliftedThreeTermDegreeOneCycleEquiv
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) :
    NatCycle (uliftedThreeTermNatChain A) 1 ≃ AbelianCycle A where
  toFun x := ⟨x.1.down, (uliftedThreeTerm_degree_one_kernel_iff A x.1).mp x.2⟩
  invFun x := ⟨ULift.up x.1, (uliftedThreeTerm_degree_one_kernel_iff A (ULift.up x.1)).mpr x.2⟩
  left_inv x := by
    apply Subtype.ext
    exact ULift.up_down x.1
  right_inv x := by
    apply Subtype.ext
    rfl

/-- The lifted degree-one homology relation is exactly the original relation. -/
theorem uliftedThreeTerm_degree_one_homologous_iff
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀)
    (x y : NatCycle (uliftedThreeTermNatChain A) 1) :
    NatHomologous (uliftedThreeTermNatChain A) 1 x y ↔
      AbelianHomologous A (uliftedThreeTermDegreeOneCycleEquiv A x)
        (uliftedThreeTermDegreeOneCycleEquiv A y) := by
  constructor
  · rintro ⟨b, hb⟩
    refine ⟨b.down, ?_⟩
    have hd := congrArg ULift.down hb
    change y.1.down = x.1.down +
      (natDegreeBoundary (uliftedThreeTermNatChain A) 2 b).down at hd
    rw [uliftedThreeTerm_boundary_two_down_eq A b] at hd
    exact hd
  · rintro ⟨b, hb⟩
    refine ⟨ULift.up b, ?_⟩
    apply (Equiv.ulift).injective
    change y.1.down = x.1.down +
      (natDegreeBoundary (uliftedThreeTermNatChain A) 2 (ULift.up b)).down
    rw [uliftedThreeTerm_boundary_two_down_eq A (ULift.up b)]
    exact hb

/--
The degree-one homology of the common-universe lifted complex is equivalent to
the original arbitrary-universe middle homology quotient.
-/
def uliftedThreeTermDegreeOneHomologyEquiv
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) :
    NatHomologyQuotient (uliftedThreeTermNatChain A) 1 ≃ AbelianHomologyQuotient A where
  toFun := Quotient.map (uliftedThreeTermDegreeOneCycleEquiv A)
    (by
      intro x y h
      exact (uliftedThreeTerm_degree_one_homologous_iff A x y).mp h)
  invFun := Quotient.map (uliftedThreeTermDegreeOneCycleEquiv A).symm
    (by
      intro x y h
      change AbelianHomologous A x y at h
      change NatHomologous (uliftedThreeTermNatChain A) 1
        ((uliftedThreeTermDegreeOneCycleEquiv A).symm x)
        ((uliftedThreeTermDegreeOneCycleEquiv A).symm y)
      apply (uliftedThreeTerm_degree_one_homologous_iff A
        ((uliftedThreeTermDegreeOneCycleEquiv A).symm x)
        ((uliftedThreeTermDegreeOneCycleEquiv A).symm y)).mpr
      simpa using h)
  left_inv := by
    intro q
    refine Quotient.inductionOn q ?_
    intro x
    change Quotient.mk _ ((uliftedThreeTermDegreeOneCycleEquiv A).symm
      (uliftedThreeTermDegreeOneCycleEquiv A x)) = Quotient.mk _ x
    rw [Equiv.symm_apply_apply]
  right_inv := by
    intro q
    refine Quotient.inductionOn q ?_
    intro x
    change Quotient.mk _ (uliftedThreeTermDegreeOneCycleEquiv A
      ((uliftedThreeTermDegreeOneCycleEquiv A).symm x)) = Quotient.mk _ x
    rw [Equiv.apply_symm_apply]

end HomologyGate
