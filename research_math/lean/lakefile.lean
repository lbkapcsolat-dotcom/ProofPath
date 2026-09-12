import Lake

open Lake DSL

package ResearchMathP0 where
  version := v!"0.1.0"
  keywords := #["math", "formal-proof", "verification"]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "v4.33.1"

@[default_target]
lean_lib ResearchMathP0
