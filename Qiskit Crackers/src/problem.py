"""The Phase 1 circuit: a star-shaped GHZ state.

H on qubit 0, then CX(0, i) for every other qubit. Most coupling maps don't connect
qubit 0 to everything, so the transpiler has to add SWAPs and the coupling map
actually changes the result. The ideal output is easy: all zeros or all ones, 50/50.
"""
from qiskit import QuantumCircuit


def star_ghz_circuit(n):
    qc = QuantumCircuit(n, n, name=f"ghz_star_{n}")
    qc.h(0)
    for i in range(1, n):
        qc.cx(0, i)
    qc.measure(range(n), range(n))
    return qc


def exact_reference(n):
    return {"0" * n: 0.5, "1" * n: 0.5}
