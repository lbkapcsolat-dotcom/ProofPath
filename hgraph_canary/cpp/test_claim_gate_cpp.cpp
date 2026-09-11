#include "claim_gate_cpp.h"

#include <hgraph/lib/testing/eval_node.h>
#include <hgraph/types/metadata/type_registry.h>

#include <array>
#include <iostream>
#include <stdexcept>
#include <string>

using ess::hgraph_canary::ClaimGateCpp;
using hgraph::Bool;
using hgraph::Int;
using hgraph::Str;

namespace
{
    constexpr const char *WOLFRAM_VECTOR =
        "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM"
        "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "PPPPIIIPPPPPIIIPPPPPIIIPPPPPIIIP"
        "CCCCCCCCCCCCCCCCOOOOOOOOPPPPIIIP";

    char decision_code(const Str &decision)
    {
        if (decision == "HOLD:MISSING_CURRENT_POINTER") return 'M';
        if (decision == "HOLD:AUTHORITY_DRIFT") return 'A';
        if (decision == "HOLD:CLAIM_EXCEEDS_EVIDENCE") return 'C';
        if (decision == "HOLD:PRODUCTION_OVERCLAIM") return 'O';
        if (decision == "HOLD:IRREVERSIBLE_WITHOUT_HUMAN_GATE") return 'I';
        if (decision == "PASS") return 'P';
        throw std::runtime_error("unknown decision: " + decision);
    }
}

int main()
{
    auto &registry = hgraph::TypeRegistry::instance();
    (void)registry.register_scalar<Bool>("bool");
    (void)registry.register_scalar<Int>("int");
    (void)registry.register_scalar<Str>("str");

    const std::array<Bool, 2> bools{false, true};
    const std::array<Int, 2> ranks{Int{3}, Int{6}};

    std::string observed;
    observed.reserve(256);

    for (const Bool current_pointer_present : bools)
    for (const Bool pointer_matches_root : bools)
    for (const Int requested_claim_rank : ranks)
    for (const Int evidence_level_rank : ranks)
    for (const Bool independent_validation : bools)
    for (const Bool irreversible_action : bools)
    for (const Bool human_gate : bools)
    for (const Bool rollback_plan : bools)
    {
        const auto result = hgraph::testing::eval_node<ClaimGateCpp>(
            hgraph::testing::values<Bool>(current_pointer_present),
            hgraph::testing::values<Bool>(pointer_matches_root),
            hgraph::testing::values<Int>(requested_claim_rank),
            hgraph::testing::values<Int>(evidence_level_rank),
            hgraph::testing::values<Bool>(independent_validation),
            hgraph::testing::values<Bool>(irreversible_action),
            hgraph::testing::values<Bool>(human_gate),
            hgraph::testing::values<Bool>(rollback_plan));

        if (result.size() != 1 || !result.front().has_value())
        {
            std::cerr << "unexpected eval_node output cardinality\n";
            return 2;
        }
        observed.push_back(decision_code(result.front().value()));
    }

    std::cout << "STATE_COUNT=" << observed.size() << '\n';
    std::cout << "OBSERVED_VECTOR=" << observed << '\n';
    std::cout << "EXPECTED_VECTOR=" << WOLFRAM_VECTOR << '\n';

    if (observed != WOLFRAM_VECTOR)
    {
        std::cerr << "WOLFRAM_PARITY_MISMATCH\n";
        return 1;
    }

    std::cout << "WOLFRAM_PARITY_256_256=PASS\n";
    return 0;
}
