"""Scores the scanner, and runs it on a couple of public repos.

The labelled fixtures carry their own answers: put a comment on the line that should be flagged,

    key = rsa.generate_private_key(...)  # EXPECT: RSA

A finding counts as a true positive if file, line and family all match a marker. A finding with
no marker is a false positive, and a marker with no finding is a false negative.

Public repos have no labels, so for those we report:
  - scan time and file/line counts
  - canary recall: copy the known-bad fixtures into a throwaway copy of the repo and check
    the scanner still finds them (synthetic, but it's measured)
  - precision: findings get written to data/processed/review_<repo>.csv for someone to label
    by hand (is_true_positive = 1 or 0). It's computed once that column is filled in.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pandas as pd

from .scanner import scan_path

PUBLIC_REPOS = {
    "requests": "https://github.com/psf/requests.git",
    "flask": "https://github.com/pallets/flask.git",
}
REVIEW_COLUMNS = ["file", "line", "family", "matched", "usage", "severity", "snippet", "is_true_positive"]
EXPECT_RE = re.compile(r"#\s*EXPECT:\s*(RSA|DSA|DH|ECC)\b")


def load_expectations(root):
    root = Path(root)
    expected = set()
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = EXPECT_RE.search(line)
            if match:
                expected.add((rel, lineno, match.group(1)))
    return expected


def prf(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    if precision + recall:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
    }


def score(findings, expected):
    predicted = {(f.file, f.line, f.family) for f in findings}
    hits = predicted & expected
    extra = predicted - expected
    missed = expected - predicted

    per_family = []
    families = sorted({key[2] for key in predicted | expected})
    for fam in families:
        p = {k for k in predicted if k[2] == fam}
        e = {k for k in expected if k[2] == fam}
        per_family.append({"family": fam, **prf(len(p & e), len(p - e), len(e - p))})

    return {
        "overall": prf(len(hits), len(extra), len(missed)),
        "per_family": per_family,
        "false_positives": sorted(extra),
        "false_negatives": sorted(missed),
    }


def ensure_repo(name, url, cache_dir):
    """Returns (path, None) if the repo is already here or clones fine, else (None, reason)."""
    dest = Path(cache_dir) / name
    if dest.exists():
        return dest, None

    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["git", "clone", "--depth", "1", url, str(dest)],
                       check=True, capture_output=True, text=True, timeout=600)
    except (subprocess.SubprocessError, OSError) as err:
        msg = str(err).strip()
        reason = msg.splitlines()[0][:200] if msg else "clone failed"
        return None, reason
    return dest, None


def canary_recall(repo_path, fixtures, name, work_dir):
    work = Path(work_dir) / f"{name}_canary"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(repo_path, work, ignore=shutil.ignore_patterns(".git"))
    shutil.copytree(fixtures, work / "_canary")

    expected = {(f"_canary/{rel}", line, fam) for rel, line, fam in load_expectations(fixtures)}
    report = scan_path(work)
    return score(report.findings, expected)["overall"]["recall"]


def precision_from_review(review_file):
    df = pd.read_csv(review_file, dtype=str).fillna("")
    labelled = df[df["is_true_positive"].str.strip() != ""]
    if labelled.empty:
        return None, 0
    is_tp = labelled["is_true_positive"].str.strip().str.lower().isin(["1", "y", "yes", "true"])
    return round(float(is_tp.mean()), 3), len(labelled)


def evaluate_repo(name, repo_path, fixtures, processed_dir, work_dir):
    report = scan_path(repo_path)

    # don't overwrite the sheet if someone has already started labelling it
    review_file = Path(processed_dir) / f"review_{name}.csv"
    if not review_file.exists():
        rows = []
        for f in report.findings:
            rows.append({"file": f.file, "line": f.line, "family": f.family, "matched": f.matched,
                         "usage": f.usage, "severity": f.severity, "snippet": f.snippet,
                         "is_true_positive": ""})
        pd.DataFrame(rows, columns=REVIEW_COLUMNS).to_csv(review_file, index=False)

    precision, reviewed = precision_from_review(review_file)
    return {
        "files": report.files_scanned,
        "lines": report.lines_scanned,
        "scan_time_s": report.elapsed_s,
        "findings": len(report.findings),
        "canary_recall": round(canary_recall(repo_path, fixtures, name, work_dir), 3),
        "precision": precision,
        "reviewed_findings": reviewed,
    }
