#ifndef ESS_HGRAPH_CLAIM_GATE_CPP_H
#define ESS_HGRAPH_CLAIM_GATE_CPP_H

#include <hgraph/types/static_node.h>

namespace ess::hgraph_canary
{
    struct ClaimGateCpp
    {
        static constexpr auto name = "ess_claim_gate_cpp";

        static void eval(
            hgraph::In<"current_pointer_present", hgraph::TS<hgraph::Bool>> current_pointer_present,
            hgraph::In<"pointer_matches_root", hgraph::TS<hgraph::Bool>> pointer_matches_root,
            hgraph::In<"requested_claim_rank", hgraph::TS<hgraph::Int>> requested_claim_rank,
            hgraph::In<"evidence_level_rank", hgraph::TS<hgraph::Int>> evidence_level_rank,
            hgraph::In<"independent_validation", hgraph::TS<hgraph::Bool>> independent_validation,
            hgraph::In<"irreversible_action", hgraph::TS<hgraph::Bool>> irreversible_action,
            hgraph::In<"human_gate", hgraph::TS<hgraph::Bool>> human_gate,
            hgraph::In<"rollback_plan", hgraph::TS<hgraph::Bool>> rollback_plan,
            hgraph::Out<hgraph::TS<hgraph::Str>> out)
        {
            if (!current_pointer_present.value())
            {
                out.set(hgraph::Str{"HOLD:MISSING_CURRENT_POINTER"});
                return;
            }

            if (!pointer_matches_root.value())
            {
                out.set(hgraph::Str{"HOLD:AUTHORITY_DRIFT"});
                return;
            }

            if (requested_claim_rank.value() > evidence_level_rank.value())
            {
                out.set(hgraph::Str{"HOLD:CLAIM_EXCEEDS_EVIDENCE"});
                return;
            }

            if (requested_claim_rank.value() >= hgraph::Int{6} && !independent_validation.value())
            {
                out.set(hgraph::Str{"HOLD:PRODUCTION_OVERCLAIM"});
                return;
            }

            if (irreversible_action.value() && !(human_gate.value() && rollback_plan.value()))
            {
                out.set(hgraph::Str{"HOLD:IRREVERSIBLE_WITHOUT_HUMAN_GATE"});
                return;
            }

            out.set(hgraph::Str{"PASS"});
        }
    };
}

#endif
