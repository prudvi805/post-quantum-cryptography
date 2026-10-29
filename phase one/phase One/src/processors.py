"""Loads the processor configs and builds the noise model for the simulator."""
import json
from pathlib import Path

PROCESSOR_DIR = Path(__file__).resolve().parent.parent / "processors"


def load_processor(name):
    # name is "A" or "B"
    path = PROCESSOR_DIR / f"processor_{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def coupling_edges(cfg):
    # the transpiler cares about CX direction, so give it both directions of every edge
    edges = set()
    for a, b in cfg["coupling_map"]:
        edges.add((a, b))
        edges.add((b, a))
    return [list(e) for e in sorted(edges)]


def build_noise_model(cfg):
    # imported here so the scanner still works without qiskit installed
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

    noise = cfg["noise"]
    model = NoiseModel()
    model.add_all_qubit_quantum_error(depolarizing_error(noise["p_1q"], 1), noise["gates_1q"])
    model.add_all_qubit_quantum_error(depolarizing_error(noise["p_2q"], 2), ["cx"])

    p = noise["p_readout"]
    model.add_all_qubit_readout_error(ReadoutError([[1 - p, p], [p, 1 - p]]))
    return model
