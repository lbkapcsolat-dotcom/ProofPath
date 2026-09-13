import NatIndexedHomologyGate
import Mathlib.Algebra.Group.ULift

namespace HomologyGate

set_option autoImplicit false

universe u₂ u₁ u₀ ua ub w

/-- Lift an additive homomorphism across arbitrary universe lifts. -/
private def uliftAddHom
    {α : Type ua} {β : Type ub}
    [AddCommGroup α] [AddCommGroup β]
    (f : α →+ β) : ULift.{w} α →+ ULift.{w} β where
  toFun x := ULift.up (f x.down)
  map_zero' := by rfl
  map_add' := by intro x y; rfl

/--
A common-universe carrier for an arbitrary-universe three-term chain complex.
The original carriers are preserved exactly behind `ULift` wrappers.
-/
@[reducible] def ULiftedThreeTermCarrier
    (C₂ : Type u₂) (C₁ : Type u₁) (C₀ : Type u₀) :
    Nat → Type (max u₂ (max u₁ u₀))
  | 0 => ULift.{max u₂ (max u₁ u₀)} C₀
  | 1 => ULift.{max u₂ (max u₁ u₀)} C₁
  | 2 => ULift.{max u₂ (max u₁ u₀)} C₂
  | _ => PUnit

instance uliftedThreeTermCarrierAddCommGroup
    (C₂ : Type u₂) (C₁ : Type u₁) (C₀ : Type u₀)
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (n : Nat) : AddCommGroup (ULiftedThreeTermCarrier C₂ C₁ C₀ n) := by
  cases n with
  | zero => infer_instance
  | succ n =>
      cases n with
      | zero => infer_instance
      | succ n =>
          cases n with
          | zero => infer_instance
          | succ n => infer_instance

/-- `boundary n` is the lifted `d_{n+1}` for the original three-term model. -/
def uliftedThreeTermBoundary
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) :
    (n : Nat) → ULiftedThreeTermCarrier C₂ C₁ C₀ (Nat.succ n) →+
      ULiftedThreeTermCarrier C₂ C₁ C₀ n
  | 0 => uliftAddHom A.boundary₁
  | 1 => uliftAddHom A.boundary₂
  | Nat.succ (Nat.succ _) => 0

/--
Natural-number indexed realization of an arbitrary-universe three-term model.
-/
def uliftedThreeTermNatChain
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀) :
    NatIndexedChainData (ULiftedThreeTermCarrier C₂ C₁ C₀) where
  boundary := uliftedThreeTermBoundary A
  boundary_sq := by
    intro n x
    cases n with
    | zero =>
        change ULift.up (A.boundary₁ (A.boundary₂ x.down)) = 0
        rw [A.boundary_sq]
        rfl
    | succ n =>
        cases n with
        | zero => simp [uliftedThreeTermBoundary]
        | succ n => simp [uliftedThreeTermBoundary]

/-- Lowering the lifted degree-one differential recovers `boundary₁`. -/
theorem uliftedThreeTerm_boundary_one_down_eq
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀)
    (x : ULiftedThreeTermCarrier C₂ C₁ C₀ 1) :
    (natDegreeBoundary (uliftedThreeTermNatChain A) 1 x).down =
      A.boundary₁ x.down := by
  rfl

/-- Lowering the lifted degree-two differential recovers `boundary₂`. -/
theorem uliftedThreeTerm_boundary_two_down_eq
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀)
    (x : ULiftedThreeTermCarrier C₂ C₁ C₀ 2) :
    (natDegreeBoundary (uliftedThreeTermNatChain A) 2 x).down =
      A.boundary₂ x.down := by
  rfl

/-- Lifted degree-one cycles are exactly original middle-degree cycles. -/
theorem uliftedThreeTerm_degree_one_kernel_iff
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀)
    (x : ULiftedThreeTermCarrier C₂ C₁ C₀ 1) :
    NatInKernel (uliftedThreeTermNatChain A) 1 x ↔
      AbelianInKernel A x.down := by
  change ULift.up (A.boundary₁ x.down) = 0 ↔ A.boundary₁ x.down = 0
  constructor
  · intro h
    have hd := congrArg ULift.down h
    simpa using hd
  · intro h
    simpa [h]

/-- Lifted degree-one boundaries are exactly original middle-degree boundaries. -/
theorem uliftedThreeTerm_degree_one_image_iff
    {C₂ : Type u₂} {C₁ : Type u₁} {C₀ : Type u₀}
    [AddCommGroup C₂] [AddCommGroup C₁] [AddCommGroup C₀]
    (A : AbelianChainData C₂ C₁ C₀)
    (x : ULiftedThreeTermCarrier C₂ C₁ C₀ 1) :
    NatInImage (uliftedThreeTermNatChain A) 1 x ↔
      AbelianInImage A x.down := by
  constructor
  · rintro ⟨y, hy⟩
    refine ⟨y.down, ?_⟩
    change ULift.up (A.boundary₂ y.down) = x at hy
    have hd := congrArg ULift.down hy
    simpa using hd
  · rintro ⟨y, hy⟩
    refine ⟨ULift.up y, ?_⟩
    change ULift.up (A.boundary₂ y) = x
    rw [hy]
    exact ULift.up_down x

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
    simpa using hd
  · rintro ⟨b, hb⟩
    refine ⟨ULift.up b, ?_⟩
    apply ULift.ext
    simpa using hb

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
