import Lake
open Lake DSL

package schumannDiscreteLyapunov where

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @
    "0df444a360eaa60ab8c11dca51a86af692955474"

@[default_target]
lean_lib SchumannDiscreteLyapunov where
  roots := #[`SchumannDiscreteLyapunov]
