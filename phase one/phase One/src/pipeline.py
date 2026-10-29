"""Runs everything and writes results/tables, results/figures and report.md.

  1. scanner on the labelled fixtures (precision / recall / F1, migration plan)
  2. Phase 1 benchmark: Processor A (5 qubits) vs Processor B (9 qubits), GHZ sizes 3-5
  3. scanner on public repos (scan time, canary recall, precision once reviewed)
  4. report.md

From the project root:
    python -m src.pipeline                  # all of it (needs qiskit + network)
    python -m src.pipeline --skip-repos     # no network
    python -m src.pipeline --skip-quantum   # scanner only, no qiskit
"""
import argparse
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
PROCESSED = ROOT / "data" / "processed"
FIXTURES = ROOT / "data" / "raw" / "ground_truth"
REPO_CACHE = ROOT / "data" / "raw" / "repos"
CANARY_WORK = ROOT / "data" / "raw" / "canary_work"
REPORT = ROOT / "report.md"

SIZES = (3, 4, 5)
HEAD_COLS = ["processor", "physical_qubits", "depth_routed", "depth_all_to_all", "cx_routed",
             "cx_all_to_all", "cx_overhead", "swap_est", "p_success_ideal", "p_success_noisy",
             "hellinger_noisy"]


def quantum_benchmark(sizes=SIZES):
    # imported here so --skip-quantum works without qiskit
    from .metrics import benchmark
    from .problem import star_ghz_circuit
    from .processors import load_processor

    rows = []
    for name in ("A", "B"):
        cfg = load_processor(name)
        for n in sizes:
            result = benchmark(star_ghz_circuit(n), cfg, n)
            rows.append({"processor": name, "physical_qubits": cfg["num_qubits"],
                         "logical_qubits": n, **result})
    return pd.DataFrame(rows)


def scanner_fixture_eval():
    from .evaluate import load_expectations, score
    from .scanner import scan_path

    report = scan_path(FIXTURES)
    return report, score(report.findings, load_expectations(FIXTURES))


def repo_evaluation():
    from .evaluate import PUBLIC_REPOS, ensure_repo, evaluate_repo

    rows = []
    for name, url in PUBLIC_REPOS.items():
        path, err = ensure_repo(name, url, REPO_CACHE)
        if path is None:
            rows.append({"repo": name, "status": f"not scanned: {err}"})
            continue
        stats = evaluate_repo(name, path, FIXTURES, PROCESSED, CANARY_WORK)
        rows.append({"repo": name, "status": "scanned", **stats})
    return pd.DataFrame(rows)


def migration_table(findings_df):
    cols = ["family", "usage", "replacement", "findings"]
    if findings_df.empty:
        return pd.DataFrame(columns=cols)
    grouped = findings_df.groupby(["family", "usage", "replacement"]).size()
    return grouped.reset_index(name="findings")


def to_markdown(df):
    """Tiny markdown table writer so we don't need the tabulate package."""
    if df is None or len(df) == 0:
        return "_No data._\n"

    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |",
             "|" + "|".join(["---"] * len(cols)) + "|"]

    # astype(object) so ints stay ints instead of being upcast to floats row by row
    for row in df.astype(object).itertuples(index=False):
        cells = []
        for value in row:
            if value is None or (isinstance(value, float) and pd.isna(value)):
                cells.append("")
            elif isinstance(value, float):
                cells.append(f"{value:.3f}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def interpret(head):
    a = head[head["processor"] == "A"].iloc[0]
    b = head[head["processor"] == "B"].iloc[0]

    paras = [
        f"Routing the 5-qubit star GHZ circuit needs {int(a.cx_routed)} CX gates on Processor A "
        f"(depth {int(a.depth_routed)}) and {int(b.cx_routed)} on Processor B "
        f"(depth {int(b.depth_routed)})."
    ]

    if a.cx_overhead == b.cx_overhead:
        paras.append(f"Both processors add the same routing overhead of {int(a.cx_overhead)} CX gates "
                     "over the all-to-all baseline, so connectivity costs the same on this circuit.")
    else:
        better, worse = ("A", "B") if a.cx_overhead < b.cx_overhead else ("B", "A")
        low, high = sorted([int(a.cx_overhead), int(b.cx_overhead)])
        paras.append(f"Processor {better} adds fewer routing CX gates than Processor {worse} "
                     f"({low} vs {high}, roughly {low // 3} vs {high // 3} SWAPs), so its coupling "
                     "map suits this circuit better.")

    paras.append(f"Under identical synthetic noise, the GHZ success probability is "
                 f"{a.p_success_noisy:.3f} on A and {b.p_success_noisy:.3f} on B, against ideal values "
                 f"of {a.p_success_ideal:.3f} and {b.p_success_ideal:.3f}. The drop from ideal to noisy "
                 "comes from the two-qubit gates in each routed circuit, so the processor with fewer "
                 "routed CX gates loses less fidelity.")
    return paras


def write_report(scan_report, scan_result, per_family, migration, q_df, head, repo_df, figures):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    out = []

    out.append(f"# Phase 1 Report: Cryptographic Inventory & Migration Scanner\n\n"
               f"_Generated {now} by `python -m src.pipeline`. Every number here is produced by "
               f"the code in `src/`._\n")

    out.append("## 1. Problem and domain\n\n"
               "Domain: Post-Quantum Cryptography (Quantum-Safe Systems). The scanner flags "
               "quantum-vulnerable RSA, DSA, DH and ECC usage in Python source and maps each finding "
               "to NIST FIPS 203 (ML-KEM) or FIPS 204 (ML-DSA). The Phase 1 Processor A and B "
               "benchmark is reported in section 2.\n")

    # --- section 2: processor benchmark
    out.append("## 2. Processor A vs Processor B benchmark\n")
    if head is None:
        out.append("_Skipped in this run (`--skip-quantum`)._\n")
    else:
        out.append("Circuit: star-shaped GHZ state (H on qubit 0, then CX from qubit 0 to every other "
                   "qubit), measured in the computational basis. Exact reference: probability 1/2 each "
                   "for the all-zeros and all-ones outcomes. Both processors use basis {rz, sx, x, cx}, "
                   "optimization level 1, seed 42, 4096 shots, and identical synthetic noise "
                   "(1q depolarizing 0.1%, 2q depolarizing 0.5%, readout 1%).\n")
        out.append("### 2.1 Headline comparison (5 logical qubits)\n")
        out.append(to_markdown(head[HEAD_COLS]))
        out.append("Column definitions: `cx_overhead` is routed CX minus all-to-all CX; `swap_est` is "
                   "`cx_overhead / 3`; `p_success` is the probability of the two GHZ outcomes.\n")
        out.append("### 2.2 Interpretation\n")
        out.append("\n\n".join(interpret(head)) + "\n")
        out.append("### 2.3 Scaling across GHZ sizes\n")
        scaling_cols = ["processor", "logical_qubits", "depth_routed", "cx_routed", "cx_overhead",
                        "p_success_noisy", "hellinger_noisy"]
        out.append(to_markdown(q_df[scaling_cols]))

    # --- section 3: scanner
    out.append("## 3. Cryptographic inventory scanner\n")
    out.append("### 3.1 Accuracy on the labelled fixture corpus\n")
    overall = {"files": scan_report.files_scanned, "lines": scan_report.lines_scanned,
               "scan_time_s": scan_report.elapsed_s, **scan_result["overall"]}
    out.append(to_markdown(pd.DataFrame([overall])))
    out.append("Per family:\n")
    out.append(to_markdown(per_family))

    misses = scan_result["false_negatives"]
    extras = scan_result["false_positives"]
    miss_text = ", ".join(f"`{f}:{line}` ({fam})" for f, line, fam in misses) or "none"
    extra_text = ", ".join(f"`{f}:{line}` ({fam})" for f, line, fam in extras) or "none"
    out.append(f"False negatives ({len(misses)}): {miss_text}. The known miss is a call through an "
               "internal wrapper library, which the scanner can't resolve without the library source.\n")
    out.append(f"False positives ({len(extras)}): {extra_text}.\n")

    out.append("### 3.2 Migration plan\n")
    out.append("Each finding maps to a replacement: key establishment and encryption move to "
               "ML-KEM-768 (FIPS 203); signatures move to ML-DSA-65 (FIPS 204). Where usage can't be "
               "inferred, both are listed.\n")
    out.append(to_markdown(migration))

    out.append("### 3.3 Public repositories\n")
    if repo_df is None:
        out.append("_Skipped in this run (`--skip-repos`)._\n")
    else:
        wanted = ["repo", "status", "files", "lines", "scan_time_s", "findings", "canary_recall",
                  "precision", "reviewed_findings"]
        out.append(to_markdown(repo_df[[c for c in wanted if c in repo_df.columns]]))
        out.append("`canary_recall` is measured by inserting known positive snippets into a copy of each "
                   "repo. `precision` is computed from the manual review sheets in "
                   "`data/processed/review_<repo>.csv`; it reads `pending` until those sheets are "
                   "filled in (is_true_positive = 1 or 0).\n")

    # --- figures, limitations, reproduce
    out.append("## 4. Figures\n")
    for fig in figures:
        rel = Path(fig).relative_to(ROOT).as_posix()
        out.append(f"![{Path(fig).stem}]({rel})\n")

    out.append("## 5. Limitations\n")
    out.append("The labelled corpus is small and was written for this project, so its precision and "
               "recall are optimistic compared with a large, independently labelled set. The scanner "
               "only looks at Python, resolves calls through direct imports (not wrapper libraries), "
               "and guesses usage from names and nearby text, so some findings will be labelled "
               "`unknown`. The SWAP count is an estimate derived from CX overhead. Noise is the "
               "synthetic model from the problem specification, not a calibrated device model.\n")

    out.append("## 6. Reproduce\n")
    out.append("```\npip install -r requirements.txt\npython -m src.pipeline\n```\n"
               "Or open `main.ipynb` and run all cells. All stochastic components use seed 42.\n")

    REPORT.write_text("\n".join(out), encoding="utf-8")


def run_all(skip_quantum=False, skip_repos=False, log=print):
    from . import visualization as viz
    from .processors import load_processor

    for folder in (TABLES, FIGURES, PROCESSED):
        folder.mkdir(parents=True, exist_ok=True)

    start = time.time()
    figures = []

    # 1. scanner on the fixtures
    log("[1/4] Scanner on labelled fixture corpus")
    scan_report, scan_result = scanner_fixture_eval()
    findings_df = pd.DataFrame([asdict(f) for f in scan_report.findings])
    per_family = pd.DataFrame(scan_result["per_family"])
    migration = migration_table(findings_df)

    findings_df.to_csv(TABLES / "scanner_findings_fixtures.csv", index=False)
    per_family.to_csv(TABLES / "scanner_metrics_by_family.csv", index=False)
    migration.to_csv(TABLES / "migration_plan.csv", index=False)
    figures.append(viz.plot_scanner(per_family, findings_df, FIGURES / "scanner_metrics.png"))

    # 2. processor benchmark
    q_df = None
    head = None
    if skip_quantum:
        log("[2/4] Quantum benchmark skipped (--skip-quantum)")
    else:
        log("[2/4] Phase 1 benchmark: Processor A vs Processor B (star GHZ, sizes 3 to 5)")
        q_df = quantum_benchmark()
        head = q_df[q_df["logical_qubits"] == max(SIZES)].reset_index(drop=True)
        q_df.to_csv(TABLES / "quantum_benchmark_all_sizes.csv", index=False)
        head.to_csv(TABLES / "comparison_5_logical_qubits.csv", index=False)

        for name in ("A", "B"):
            figures.append(viz.plot_coupling_map(load_processor(name),
                                                 FIGURES / f"coupling_map_processor_{name}.png",
                                                 viz.PALETTE[name]))
        figures.append(viz.plot_scaling(q_df, FIGURES / "scaling_depth_cx_success.png"))
        figures.append(viz.plot_headline(head, FIGURES / "comparison_5q_bars.png"))

    # 3. public repos
    repo_df = None
    if skip_repos:
        log("[3/4] Public repositories skipped (--skip-repos)")
    else:
        log("[3/4] Public repositories: scan time, canary recall, review sheets")
        repo_df = repo_evaluation()
        repo_df.to_csv(TABLES / "public_repos.csv", index=False)
        scanned = repo_df[repo_df["status"] == "scanned"] if "status" in repo_df else repo_df
        if len(scanned):
            figures.append(viz.plot_repo_timing(scanned, FIGURES / "repo_scan_time.png"))

    # 4. report
    log("[4/4] Writing report.md")
    write_report(scan_report, scan_result, per_family, migration, q_df, head, repo_df, figures)
    log(f"Done in {time.time() - start:.1f}s. See report.md and results/.")

    return {"scan_report": scan_report, "scanner_eval": scan_result, "quantum": q_df,
            "comparison_5q": head, "repos": repo_df, "figures": figures}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-quantum", action="store_true", help="skip the Qiskit benchmark")
    parser.add_argument("--skip-repos", action="store_true", help="skip cloning public repos")
    args = parser.parse_args()
    run_all(skip_quantum=args.skip_quantum, skip_repos=args.skip_repos)


if __name__ == "__main__":
    main()
