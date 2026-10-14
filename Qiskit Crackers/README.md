# Cryptographic Inventory & Migration Scanner (Post-Quantum Cryptography)

**Domain:** Post-Quantum Cryptography (Quantum-Safe Systems)
**Problem statement (selected, one only):** Cryptographic Inventory & Migration Scanner. Build a static analysis scanner that inspects a codebase for quantum-vulnerable cryptography (RSA, DSA, DH, ECC), flags migration paths to NIST FIPS 203 and FIPS 204, and reports precision, recall and scan time on public open-source repositories.

## What this project does

1. **Scanner (the problem statement).** `src/scanner.py` parses Python source with the `ast` module, resolves import aliases, and flags calls into RSA, DSA, DH and ECC libraries (pyca/cryptography, PyCryptodome, pure-python `rsa`, `ecdsa`, PyNaCl). A second, pattern-based layer flags JWT and TLS algorithm identifiers such as `RS256`, `ES256` and `EdDSA`. Each finding gets a usage class (signature, key establishment, unknown), a severity, and a migration target: ML-DSA-65 (FIPS 204) for signatures, ML-KEM-768 (FIPS 203) for key establishment.
2. **Evaluation.** Precision, recall and F1 on a labelled corpus (`data/raw/ground_truth/`). Scan time and canary recall on public repositories (Requests and Flask by default).
3. **Phase 1 benchmark (Processor A vs Processor B).** A star-shaped GHZ circuit is transpiled onto two separately defined processors, A (5 qubits) and B (9 qubits), with identical basis gates, optimization level, seed, shots and synthetic noise. The results are compared on depth, CX count, SWAP overhead and noisy fidelity.

Running the pipeline produces `report.md`, CSV tables in `results/tables/`, and figures in `results/figures/`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.pipeline               # full run: scanner, Processor A/B benchmark, public repos, report.md
python -m src.pipeline --skip-repos  # no network needed
python -m src.pipeline --skip-quantum  # scanner only, no Qiskit needed
```

Or open `main.ipynb` and run all cells. The notebook calls the same pipeline and displays the report and every figure.

Run time is a few minutes on a laptop. Every stochastic component uses seed 42.

## Repository structure

```
project/
├── README.md                  this file
├── main.ipynb                 end-to-end notebook
├── requirements.txt           pinned dependencies
├── data/
│   ├── raw/
│   │   ├── ground_truth/      labelled corpus used for precision and recall (# EXPECT: markers)
│   │   ├── repos/             public repos cloned on demand (git-ignored)
│   │   └── canary_work/       temporary copies used for canary recall (git-ignored)
│   └── processed/             manual review sheets for public-repo precision
├── processors/
│   ├── processor_A.json       Processor A: participant-designed 5-qubit coupling map + config
│   └── processor_B.json       Processor B: 9-qubit heavy-hex reference + config
├── src/
│   ├── scanner.py             AST and pattern scanner, migration mapping
│   ├── evaluate.py            precision/recall/F1, public-repo evaluation
│   ├── problem.py             Phase 1 algorithm (star GHZ) and exact reference
│   ├── processors.py          loads A/B configs, builds the noise model
│   ├── routing.py             transpilation with and without the coupling map
│   ├── metrics.py             depth, CX, SWAP overhead, success and Hellinger fidelity
│   ├── visualization.py       coupling maps, comparison plots, scanner and repo plots
│   └── pipeline.py            runs everything and writes report.md
├── results/
│   ├── tables/                CSV outputs
│   └── figures/               PNG outputs
├── report.md                  generated report (overwritten on each run)
└── assets/
    └── qff_phase1_latex_images/
```

`src/scanner.py` and `src/evaluate.py` are additions for the problem statement. The `src/` files named in the Phase 1 repository specification (`problem.py`, `processors.py`, `routing.py`, `metrics.py`, `visualization.py`) carry the Phase 1 quantum benchmark.

## Scanner: method

**Detection.** The scanner resolves every call target through the file's imports before matching it. `rsa.generate_private_key` is flagged only when `rsa` was imported from a known RSA module. A local variable named `rsa` is not flagged, which keeps out a common false-positive source. The family is determined by the module (RSA, DSA, DH or ECC), and the operation name determines severity: key or parameter generation is HIGH, other use is MEDIUM. When one line matches several calls in the same family, the line is reported once.

**Usage inference.** Usage is inferred from the resolved call name and the source line. Words such as sign, verify, ECDSA, Ed25519 and DSA indicate signature use. Words such as DH, X25519, ECDH, exchange, encrypt and OAEP indicate key establishment. Anything else is `unknown`, and the report then lists both replacements.

**Migration mapping.** Signatures map to ML-DSA-65 (FIPS 204). Key establishment and encryption map to ML-KEM-768 (FIPS 203). The scanner reports the mapping; it does not rewrite code.

**Scope.** Python only. Calls through wrapper libraries cannot be resolved without their source; the labelled corpus includes one such case on purpose so that the recall figure is honest.

## Scanner: evaluation protocol

- **Labelled corpus.** Each line that should be flagged carries `# EXPECT: <FAMILY>`. A finding is a true positive only when file, line and family all match. Unmatched findings are false positives and unmatched markers are false negatives.
- **Public repositories.** These are unlabelled, so the pipeline reports three things. Scan time and file and line counts are measured directly. Canary recall is measured by copying labelled positive snippets into a temporary copy of each repository and checking that the scanner finds them. Precision requires manual review: the first run writes `data/processed/review_<repo>.csv` with one row per finding. To complete the evaluation, set `is_true_positive` to `1` or `0` for each row and rerun the pipeline. The pipeline never overwrites a review file that already exists.

## Phase 1 benchmark: design

**Processor A (5 qubits, custom).** Coupling map: (0,1), (1,2), (2,3), (1,3), (3,4). The design is a fork with a closed triangle. Node 1 is a degree-3 hub and nodes 1-2-3 form a triangle. Compared with the linear-chain and branching-tree references, it adds one edge, (1,3), so three mutually interacting qubits can be placed without a SWAP.

**Processor B (9 qubits, reference).** The heavy-hex-inspired 12-edge graph from the specification, used unchanged as the contemporary control.

**Shared configuration.** Basis gates {rz, sx, x, cx}, optimization level 1, seed 42, 4096 shots, and synthetic noise: 1-qubit depolarizing 0.1%, 2-qubit depolarizing 0.5%, readout 1%. Both processors use identical noise, so differences isolate connectivity.

**Circuit.** Star-shaped GHZ state: H on qubit 0, then CX from qubit 0 to every other qubit. Long-range fan-out makes routing matter. The exact reference is probability 1/2 for each of the all-zeros and all-ones outcomes. GHZ sizes 3, 4 and 5 are run on both processors.

**Metrics.**
- `depth_routed`, `cx_routed`: depth and CX count after routing onto the processor's coupling map.
- `cx_overhead`: routed CX count minus the CX count of an all-to-all transpilation.
- `swap_est`: `cx_overhead / 3`, since a SWAP compiles to three CX gates in this basis.
- `p_success_ideal`, `p_success_noisy`: probability of the two GHZ outcomes without and with noise.
- `hellinger_*`: Hellinger fidelity to the exact distribution.

## Limitations

- The labelled corpus is small and was written for this project, so its precision and recall are optimistic.
- The scanner covers Python only and cannot see through wrapper libraries.
- Usage inference is heuristic, so some findings are `unknown`.
- SWAP counts are estimates derived from CX overhead.
- Noise follows the synthetic model from the specification, not a calibrated device model.

## Note on scope

The problem statement is a classical static-analysis tool, while the Phase 1 specification asks for a quantum circuit benchmarked on two processors. This project delivers both: the scanner is the solution to the selected problem statement, and the processor benchmark uses a quantum circuit whose exact reference is known. Confirm with the organisers that this split matches their evaluation.
