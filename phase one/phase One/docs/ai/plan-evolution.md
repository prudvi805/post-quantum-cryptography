# Plan Evolution

**Stage 1: Scanner idea.** Start from the problem statement: a static scanner for RSA, DSA, DH and ECC, mapped to FIPS 203 and 204, evaluated on public repos.

**Stage 2: Hackathon requirements added.** The Phase 1 specification was added: two processors (A with 5 qubits, B with 9 qubits), a basis gate set, a synthetic noise model, and a fixed repository structure. This required a quantum benchmark alongside the scanner. The mismatch between a classical scanner and a quantum benchmark was noted and documented in the README.

**Stage 3: Scanner built and tested.** Implemented the AST scanner with import resolution, a pattern layer for JWT algorithms, and a labelled corpus. First results: 13 of 14 labelled positives found, no false positives, one intentional miss.

**Stage 4: Benchmark built.** Star GHZ circuit, Processor A (custom design) and Processor B (reference), identical noise and transpile settings, and sweeps over sizes 3 to 5. Written but not yet executed on the target machine, because the development environment did not have Qiskit.

**Stage 5: Reporting and evaluation.** Added `report.md` generation, figures, public-repo timing, canary recall, and review sheets for precision.

**Stage 6: Running on the user's machine.** Dependency installs, interpreter problems, and output-location questions were resolved one at a time. A scanner-only run was confirmed to produce `report.md`.

**Remaining:** full run including the quantum benchmark, public repo precision review, GitHub submission, and the closing checklist.
