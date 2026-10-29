"""
QFF 2026 Phase 2 - PS-P2 BASELINE (deliberately naive keyword matcher).

This is the official baseline that every PS-P2 team must compare against and beat.
It ignores contradictions, hybrids, aliases and metadata, and gives a flat priority.

    python baseline_classifier.py --input inventory_dev.csv --output baseline_predictions.csv
    python evaluate.py --pred baseline_predictions.csv --labels inventory_dev_labels.csv
"""
import argparse
import csv


def classify(alg: str) -> str:
    a = alg.upper()
    if not a.strip():
        return "UNKNOWN"
    if "RSA" in a or "EC" in a or "DH" in a:
        return "QUANTUM_VULNERABLE"
    if "ML-KEM" in a or "ML-DSA" in a or "SLH-DSA" in a:
        return "QUANTUM_RESISTANT"
    if "MD5" in a or "SHA-1" in a:
        return "LEGACY_BROKEN"
    if "AES" in a or "SHA" in a:
        return "SYMMETRIC_OR_HASH"
    return "UNKNOWN"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    with open(a.input, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open(a.output, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["asset_id", "predicted_label", "priority_score", "priority_rank",
                    "recommended_action", "migration_wave", "depends_on", "rationale"])
        for r in rows:
            lab = classify(r.get("algorithm", ""))
            score = {"QUANTUM_VULNERABLE": 80, "UNKNOWN": 50, "LEGACY_BROKEN": 40}.get(lab, 10)
            rank = {80: 1, 50: 2, 40: 3}.get(score, 4)
            wave = {"QUANTUM_VULNERABLE": "1", "UNKNOWN": "review"}.get(lab, "3")
            w.writerow([r["asset_id"], lab, score, rank, "baseline: no specific action", wave, "",
                        f"keyword match on algorithm='{r.get('algorithm', '')}'"])
    print(f"wrote {len(rows)} predictions to {a.output}")


if __name__ == "__main__":
    main()
