using LinearAlgebra
using Base.Threads

@assert VERSION == v"1.12.7"
@assert Threads.nthreads(:default) >= 2

println("Julia version: ", VERSION)
println("Default threads: ", Threads.nthreads(:default))
println("Interactive threads: ", Threads.nthreads(:interactive))
println("Max thread id: ", Threads.maxthreadid())
println("BLAS config: ", BLAS.get_config())
println("BLAS threads: ", BLAS.get_num_threads())

# Dense linear algebra correctness canary.
A = [4.0 1.0 2.0; 1.0 3.0 0.0; 2.0 0.0 5.0]
b = [7.0, 4.0, 9.0]
x = A \ b
residual = norm(A * x - b, Inf)
println("linear solve residual_inf = ", residual)
@assert residual < 1e-12

# Symmetric positive-semidefinite matrix consistency canary.
M = reshape(Float64.(1:16), 4, 4)
N = transpose(M) * M
@assert issymmetric(N)
@assert minimum(eigvals(Symmetric(N))) > -1e-10

# Independent exact-integer crosscheck for ALG-LIVE.
factor_product = big(3) * big(5) * big(17) * big(257) * big(65537)
mersenne32 = big(2)^32 - 1
@assert factor_product == mersenne32 == 4294967295

# Multi-threaded deterministic integer reduction.
# Do not index storage by threadid(): Julia 1.12 has multiple thread pools,
# and thread IDs are not guaranteed to fit 1:nthreads(:default).
n = 1_000_000
chunks = Threads.nthreads(:default)
partials = zeros(Int128, chunks)
Threads.@threads :static for k in 1:chunks
    lo = fld((k - 1) * n, chunks) + 1
    hi = fld(k * n, chunks)
    acc = Int128(0)
    for i in lo:hi
        acc += Int128(i)
    end
    partials[k] = acc
end
threaded_sum = sum(partials)
serial_sum = Int128(n) * (n + 1) ÷ 2
println("threaded_sum = ", threaded_sum)
println("serial_sum   = ", serial_sum)
@assert threaded_sum == serial_sum == 500000500000

println("P1-C JULIA/HPC = PASS")
println("PROOFPATH_EVIDENCE ALG-LIVE independent_exact_crosscheck factor_product=4294967295")
println("PROOFPATH_EVIDENCE HPC-LIVE hpc_computation threaded_sum=500000500000")
