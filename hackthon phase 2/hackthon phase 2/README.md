# Team Q-Safe — PS-P2: Enterprise Cryptographic Inventory and Migration Planner

**Team members:** Prudvi Narayana (Lead & Cryptographic Engineer), Team Contributors  
**Problem statement:** PS-P2 — Enterprise Cryptographic Inventory and Migration Planner  
**Phase 1 work reused:** yes (Phase 1 static code analyzer adapted as the multi-language scanner in `src/repo_scanner.py`)

---

## 1. Summary

This repository delivers an offline cryptographic inventory classifier and migration planner for **PS-P2**. It ingests inventories in the format defined by `SCHEMA.md`, applies the six official labels with deterministic rule precedence, and achieved **1.0000 Macro-F1 and accuracy** on the 150-record development set using the official `evaluate.py`. It assigns explainable 0–100 risk scores, review/migration waves, and recommended actions. The optional Phase 1 code scanner found all **18/18** planted cryptographic assets in `sample_repo/`. On the latest recorded Platform A run, the tool processed 1,000 synthetic records in **0.055 seconds**; see the benchmark evidence and power-state note below.

---

## 2. Setup — exact steps

The core tool (`run_inventory.py`), evaluator (`evaluate.py`), and test suite use only the Python standard library. The challenge kit supports Python 3.10–3.13; Python 3.13.17 was used for the verification recorded below. The kit libraries are installed to run the required environment self-test and platform tools.

```bash
# 1. Create and activate a virtual environment (Windows PowerShell)
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
# Windows Command Prompt: py -3.13 -m venv .venv
#                        .venv\Scripts\activate.bat
#
# 2. Install the challenge kit reference libraries
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 3. Verify the environment (must end with READY)
python common/env_check.py
```

If PowerShell blocks activation, use Command Prompt or invoke the virtual-environment interpreter directly as `.venv\Scripts\python.exe`.
On macOS/Linux, create and activate the environment with `python3 -m venv .venv` and `source .venv/bin/activate`.

The tool itself classifies inventories offline and does not call network services.

---

## 3. Reproduce the principal results — exact commands

All commands run directly from the repository root:

```bash
# Command 1: Mandatory CLI Interface on Development Set (produces results/predictions_dev.csv)
python run_inventory.py --input inventory_dev.csv --output results/predictions_dev.csv

# Command 2: Official Scorer (reproduces 1.0000 Macro-F1 and 0 Unsafe-Unknowns)
python evaluate.py --pred results/predictions_dev.csv --labels inventory_dev_labels.csv

# Command 3: Side-by-side comparative benchmark against official baseline
python src/benchmark_comparison.py

# Command 4: Scalability stress test on 1,000 synthetic records
python src/synthetic_generator.py

# Command 5: Optional multi-language code scanner (Phase 1 integration)
python -c "from src.repo_scanner import export_repo_inventory; export_repo_inventory('sample_repo', 'results/sample_repo_inventory.csv')"
python run_inventory.py --input results/sample_repo_inventory.csv --output results/sample_repo_predictions.csv
```

**Measured scalability run on Platform A:** 1,000 synthetic records processed in **0.055 seconds** (18,181.5 records/second) on the recorded machine. Timing varies by machine and power state; the required limit is 300 seconds.

---

## 4. Platforms used

| Platform | Machine / profile | Evidence file |
|---|---|---|
| **A** | Windows 11 (AMD64), 8 physical / 12 logical cores, 15.71 GB RAM, Python 3.13.17; recorded environment check showed on battery | [`platform_A_info.json`](platform_A_info.json) |
| **B (if used)** | *Not needed for PS-P2 data analysis track (per Guide §2)* | N/A |
| **D (optional)**| *Not needed for PS-P2 (per Guide §2)* | N/A |

---

## 5. Libraries and versions

The challenge kit supports Python 3.10–3.13. This project was verified with Python 3.13.17 and the following installed versions:
- `cryptography == 50.0.2` (reference PQC and classical primitives)
- `pqcrypto == 1.0.0` (SLH-DSA and ML-KEM bindings)
- `psutil == 7.2.2` (environment and platform tools)
- `numpy == 2.5.4`, `pandas == 3.1.0`, `matplotlib == 3.11.2` (analysis tools)

The core CLI uses only the Python standard library (`csv`, `re`, `argparse`, `sys`, `pathlib`); no third-party package is imported during classification.

---

## 6. Tests (command, expected behaviour, recorded result)

### Command:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Expected Behaviour:
Runs all 13 automated unit, contract, and robustness tests:
- `test_classifier.py` (9 tests): Validates official 6-stage rule precedence, contradiction checks (hash-as-signature, impossible key sizes), alias mapping, and hybrid detection.
- `test_prioritization.py` (3 tests): Validates 0–100 score bounds, non-zero review priority for `UNKNOWN`, and distinct priority differentiation across assets with identical algorithms.
- `test_cli.py` (1 test): Validates the mandatory CLI interface (`run_inventory.py --input --output`), output column formatting, and non-empty rationale fields.

### Recorded Result:
```text
Ran 13 tests in 0.862s
OK
```

---

## 7. Results (tables / figures, with links to files in results/)

### Official Evaluation Metrics on Development Set (150 records)
Scored using official `evaluate.py`:
- Link to raw evaluation output: [`results/evaluation_dev.json`](results/evaluation_dev.json)
- Link to predicted CSV: [`results/predictions_dev.csv`](results/predictions_dev.csv)

| Metric | Result | Benchmark Baseline | Delta / Improvement |
|---|---|---|---|
| **Overall Accuracy** | **1.0000 (100.0%)** | 0.5867 (58.67%) | **+41.33%** |
| **Headline Macro-F1** | **1.0000** | 0.4757 | **+0.5243** |
| **UNKNOWN Recall** | **1.0000** | 0.4667 | **+53.33%** |
| **Unsafe-Unknown Count** | **0** | 14 | **-14 (100% eliminated)** |
| **Hash-as-Public-Key** | **0** | 0 | **0 (Zero misclassifications)** |
| **Hybrid F1** | **1.0000** | 0.0000 | **+1.0000** |

### Scalability Stress Test (1,000 synthetic enterprise assets)
- Evidence file: [`results/benchmark_1000.json`](results/benchmark_1000.json)
- Predictions output: [`results/synthetic_1000_predictions.csv`](results/synthetic_1000_predictions.csv)
- **Time Elapsed:** **0.055 seconds** (Organizer threshold: 300 seconds)
- **Throughput:** **18,181.5 records/second** (**5,454x faster** than the 5-minute requirement)
- **Measurement note:** Platform A's recorded environment check showed it was on battery; timing is machine- and power-state-dependent.

### Multi-Language Code Scanner Validation (sample_repo/)
- Discovered Inventory: [`results/sample_repo_inventory.csv`](results/sample_repo_inventory.csv)
- Generated Predictions: [`results/sample_repo_predictions.csv`](results/sample_repo_predictions.csv)
- Discovered 18/18 planted assets across Python, Java, C, and OpenSSH (100% match with [`sample_repo_expected.csv`](sample_repo_expected.csv)).

---

## 8. Baseline used

The baseline is the organizer-supplied `baseline_classifier.py` (a naive keyword-matching classifier). 

### Headline Comparison ([`results/benchmark_comparison.csv`](results/benchmark_comparison.csv)):
```text
======================================================================
PS-P2 BENCHMARK COMPARISON: OUR TOOL vs BASELINE CLASSIFIER
======================================================================
  Overall Accuracy         | Baseline: 0.5867   | Our Tool: 1.0000   | +41.33%
  Headline Macro-F1        | Baseline: 0.4757   | Our Tool: 1.0000   | +0.5243
  UNKNOWN Recall           | Baseline: 0.4667   | Our Tool: 1.0000   | +53.33%
  Unsafe-Unknown Count     | Baseline: 14       | Our Tool: 0        | -14 (100% eliminated)
  Hash-as-Public-Key       | Baseline: 0        | Our Tool: 0        | 0 (zero error)
  Hybrid F1                | Baseline: 0.0000   | Our Tool: 1.0000   | +1.0000
======================================================================
```

Why the baseline fails:
1. Misses composite hybrid combinations (`X25519MLKEM768`), scoring 0.0000 F1 on `HYBRID`.
2. Silently misclassifies unidentifiable/contradictory records into safe categories (14 unsafe-unknown violations).
3. Lacks contradiction detection and contextual risk prioritization.

---

## 9. Known limitations

1. **Static AST Parameter Inference:** When cryptographic parameters are loaded at runtime from dynamic environment variables or configuration files, static code analysis may extract blank key sizes, falling back to conservative `UNKNOWN` or default risk ratings.
2. **Automated Remediation:** The current release infers dependencies and outputs actionable migration waves, targets, and rationales; automated AST code refactoring and PR generation are planned for future releases.
3. **Hardware-Bound Assets:** HSMs and smart cards cannot be migrated via software updates alone and require physical device lifecycle management.
