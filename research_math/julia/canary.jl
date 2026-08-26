using LinearAlgebra
using Base.Threads

@assert VERSION == v"1.12.7"
@assert Threads.nthreads() >= 2

println("Julia version: ", VERSION)
println("Julia threads: ", Threads.nthreads())
println("BLAS config: ", BLAS.get_config())
println("BLAS threads: ", BLAS.get_num_threads())

# Dense linear algebra correctness canary.
A = [4.0 1.0 2.0; 1.0 3.0 0.0; 2.0 0.0 5.0]
b = [7.0, 4.0, 9.0]
x = A \ b
residual = norm(A * x - b, Inf)
println("linear solve residual_inf = ", residual)
@assert residual < 1e-12

# Matrix multiplication consistency canary.
M = reshape(Float64.(1:16), 4, 4)
N = transpose(M) * M
@assert issymmetric(N)
@assert minimum(eigvals(Symmetric(N))) > -1e-10

# Multi-threaded deterministic integer reduction.
n = 1_000_000
partials = zeros(Int128, Threads.nthreads())
Threads.@threads :static for i in 1:n
    partials[Threads.threadid()] += Int128(i)
end
threaded_sum = sum(partials)
serial_sum = Int128(n) * (n + 1) ÷ 2
println("threaded_sum = ", threaded_sum)
println("serial_sum   = ", serial_sum)
@assert threaded_sum == serial_sum

println("P1-C JULIA/HPC = PASS")
