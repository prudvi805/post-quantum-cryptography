# Architecture Decision Records

## ADR-1: Static scanner uses Python's AST, not regular expressions
**Decision:** Parse Python with `ast` and match resolved call targets.
**Why:** Regex on source text flags comments, docstrings and local variables named `rsa`. AST matching lets the scanner ignore those.
**Consequence:** Python only. Other languages would need their own parser.

## ADR-2: Calls are resolved through imports before matching
**Decision:** A call counts only if its root name was imported from a known crypto module (for example `rsa` from `cryptography...asymmetric`).
**Why:** It removes most false positives from unrelated names.
**Consequence:** Calls through wrapper libraries are missed. The labelled corpus includes one such case (`m1_wrapper_miss.py`), so recall is reported as 13 of 14, not 100%.

## ADR-3: Migration targets follow NIST FIPS 203 and 204
**Decision:** Signatures map to ML-DSA-65 (FIPS 204). Key establishment and encryption map to ML-KEM-768 (FIPS 203). Unknown usage lists both.
**Why:** These are the NIST-standardised post-quantum replacements for the RSA, DSA, DH and ECC families in the problem statement.

## ADR-4: Precision on public repos is measured by manual review; recall by canary insertion
**Decision:** Public repos have no labels. The pipeline exports findings to `data/processed/review_<repo>.csv` for a person to mark 1 or 0. Recall is measured by copying labelled snippets into a temporary copy of each repo.
**Why:** Labelling thousands of lines automatically would be less honest than a reviewed sample. Canary recall gives a measured figure without needing labels.
**Consequence:** Precision reads "pending" until the review files are filled in.

## ADR-5: Phase 1 benchmark uses a star-shaped GHZ circuit
**Decision:** H on qubit 0, then CX from qubit 0 to every other qubit, for sizes 3 to 5.
**Why:** The fan-out gates are long-range on most coupling maps, so routing changes the compiled circuit. The ideal output is known exactly (1/2 for all-zeros and 1/2 for all-ones).

## ADR-6: Processor A is a custom design; Processor B is the reference
**Decision:** Processor A uses edges (0,1), (1,2), (2,3), (1,3), (3,4): a degree-3 hub with a closed triangle. Processor B uses the 12-edge heavy-hex reference unchanged.
**Why:** The specification allows any valid 5-qubit graph. B stays unchanged so it is a fixed control.
**Consequence:** Only A is a participant design. A more creative B would need its own justification.

## ADR-7: Identical noise and transpile settings on both processors
**Decision:** Basis {rz, sx, x, cx}, optimisation level 1, seed 42, 4096 shots, depolarizing 0.1% (1q), 0.5% (2q), readout 1%. Both processors use the same values.
**Why:** So the only difference between the processors is connectivity.

## ADR-8: Optional modes for running without Qiskit or network
**Decision:** `--skip-quantum` runs only the scanner. `--skip-repos` skips cloning.
**Why:** The scanner can be checked on any machine. Repo cloning needs network access and Git.
