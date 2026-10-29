"""Transpile a circuit, either onto the processor's coupling map or all-to-all."""
from qiskit import transpile

from .processors import coupling_edges


def route(circuit, cfg, coupled=True):
    opts = cfg["transpile"]
    kwargs = dict(
        basis_gates=opts["basis_gates"],
        optimization_level=opts["optimization_level"],
        seed_transpiler=opts["seed"],
    )
    if coupled:
        kwargs["coupling_map"] = coupling_edges(cfg)
    return transpile(circuit, **kwargs)
