"""Benchmark numbers for one circuit on one processor.

Quick key:
  *_routed          after transpiling onto the processor's coupling map
  *_all_to_all      same circuit with no coupling constraints (baseline)
  cx_overhead       routed CX count minus all-to-all CX count
  swap_est          cx_overhead // 3, since one SWAP is 3 CX in this basis
  p_success_*       chance of getting all-0 or all-1
  hellinger_*       Hellinger fidelity against the exact GHZ distribution
  *_ideal / *_noisy noiseless run vs run with the processor's noise model
"""
from qiskit.quantum_info import hellinger_fidelity
from qiskit_aer import AerSimulator

from .problem import exact_reference
from .processors import build_noise_model
from .routing import route


def count_cx(circuit):
    return int(circuit.count_ops().get("cx", 0))


def to_probs(counts):
    total = sum(counts.values())
    return {bits: c / total for bits, c in counts.items()}


def benchmark(circuit, cfg, n):
    shots = cfg["transpile"]["shots"]
    seed = cfg["transpile"]["seed"]

    routed = route(circuit, cfg, coupled=True)
    baseline = route(circuit, cfg, coupled=False)

    ideal_sim = AerSimulator(seed_simulator=seed)
    noisy_sim = AerSimulator(noise_model=build_noise_model(cfg), seed_simulator=seed)
    ideal = ideal_sim.run(routed, shots=shots).result().get_counts()
    noisy = noisy_sim.run(routed, shots=shots).result().get_counts()

    all_zeros, all_ones = "0" * n, "1" * n
    p_ideal = (ideal.get(all_zeros, 0) + ideal.get(all_ones, 0)) / shots
    p_noisy = (noisy.get(all_zeros, 0) + noisy.get(all_ones, 0)) / shots

    ref = exact_reference(n)
    cx_routed = count_cx(routed)
    cx_base = count_cx(baseline)

    return {
        "depth_routed": int(routed.depth()),
        "depth_all_to_all": int(baseline.depth()),
        "cx_routed": cx_routed,
        "cx_all_to_all": cx_base,
        "cx_overhead": cx_routed - cx_base,
        "swap_est": (cx_routed - cx_base) // 3,
        "p_success_ideal": round(p_ideal, 4),
        "p_success_noisy": round(p_noisy, 4),
        "hellinger_ideal": round(float(hellinger_fidelity(to_probs(ideal), ref)), 4),
        "hellinger_noisy": round(float(hellinger_fidelity(to_probs(noisy), ref)), 4),
    }
