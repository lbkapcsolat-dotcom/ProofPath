cmake_minimum_required(VERSION 3.25)
project(ess_hgraph_cpp_canary LANGUAGES CXX)

find_package(hgraph CONFIG REQUIRED)

add_executable(ess_hgraph_cpp_canary
    test_claim_gate_cpp.cpp
)

target_link_libraries(ess_hgraph_cpp_canary PRIVATE hgraph::core)
target_compile_features(ess_hgraph_cpp_canary PRIVATE cxx_std_23)
