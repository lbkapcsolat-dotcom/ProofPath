import Lake
open Lake DSL

package namespaceSafeEq64 where

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @
    "0df444a360eaa60ab8c11dca51a86af692955474"

@[default_target]
lean_lib NamespaceSafeEQ64 where
  roots := #[`NamespaceSafeEQ64, `HomologyGate, `AbelianHomologyGate, `NatIndexedHomologyGate, `CrossUniverseHomologyGate, `MathlibHomologicalComplexBridge, `RuntimeBindOracle]

lean_exe runtimeBindOracle where
  root := `RuntimeBindOracle
