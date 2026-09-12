import Lake
open Lake DSL

package namespaceSafeEq64 where

@[default_target]
lean_lib NamespaceSafeEQ64 where
  roots := #[`NamespaceSafeEQ64, `HomologyGate]
