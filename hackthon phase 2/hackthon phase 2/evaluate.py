"""
QFF 2026 Phase 2 - PS-P2 official evaluator.
Judges use this exact script on the hidden evaluation inventory.

    python evaluate.py --pred predictions.csv --labels inventory_dev_labels.csv [--json out.json]

Standard library only.
"""
import argparse
import csv
import json
import sys

LABELS = ["QUANTUM_VULNERABLE", "QUANTUM_RESISTANT", "HYBRID",
          "SYMMETRIC_OR_HASH", "LEGACY_BROKEN", "UNKNOWN"]
PUBLIC_KEY_LABELS = {"QUANTUM_VULNERABLE", "QUANTUM_RESISTANT", "HYBRID"}
REQUIRED_COLS = ["asset_id", "predicted_label", "priority_score", "priority_rank",
                 "recommended_action", "migration_wave", "rationale"]


def load_labels(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {r["asset_id"].strip(): r["label"].strip() for r in csv.DictReader(f)}


def load_preds(path):
    with open(path, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames or []
        rows = list(rd)
    missing_cols = [c for c in REQUIRED_COLS if c not in cols]
    preds = {}
    for r in rows:
        aid = (r.get("asset_id") or "").strip()
        if aid:
            preds[aid] = r
    return preds, missing_cols


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--json", default=None, help="optional path to write metrics as JSON")
    a = ap.parse_args()

    truth = load_labels(a.labels)
    preds, missing_cols = load_preds(a.pred)

    cm = {t: {p: 0 for p in LABELS + ["MISSING/INVALID"]} for t in LABELS}
    invalid = missing = 0
    unsafe_unknown = hash_as_pk = 0
    bad_scores = 0
    for aid, t in truth.items():
        r = preds.get(aid)
        if r is None:
            p = "MISSING/INVALID"
            missing += 1
        else:
            p = (r.get("predicted_label") or "").strip().upper()
            if p not in LABELS:
                p = "MISSING/INVALID"
                invalid += 1
            try:
                s = float(r.get("priority_score", ""))
                if not 0 <= s <= 100:
                    bad_scores += 1
            except ValueError:
                bad_scores += 1
        cm[t][p] += 1
        if t == "UNKNOWN" and p in ("SYMMETRIC_OR_HASH", "QUANTUM_RESISTANT"):
            unsafe_unknown += 1
        if t in ("SYMMETRIC_OR_HASH", "LEGACY_BROKEN") and p in PUBLIC_KEY_LABELS:
            hash_as_pk += 1

    n = len(truth)
    correct = sum(cm[l][l] for l in LABELS)
    per = {}
    for l in LABELS:
        tp = cm[l][l]
        fp = sum(cm[t][l] for t in LABELS if t != l)
        fn = sum(cm[l][p] for p in cm[l] if p != l)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        per[l] = {"precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4), "support": tp + fn}
    macro_f1 = sum(v["f1"] for v in per.values()) / len(LABELS)
    extra = [aid for aid in preds if aid not in truth]

    res = {
        "records": n,
        "accuracy": round(correct / n, 4) if n else 0.0,
        "macro_f1": round(macro_f1, 4),
        "per_class": per,
        "confusion_matrix": cm,
        "unknown_recall": per["UNKNOWN"]["recall"],
        "unsafe_unknown_count": unsafe_unknown,
        "hash_as_public_key_count": hash_as_pk,
        "missing_predictions": missing,
        "invalid_labels": invalid,
        "invalid_priority_scores": bad_scores,
        "extra_ids_not_in_inventory": len(extra),
        "missing_required_columns": missing_cols,
    }

    print("=" * 64)
    print("QFF 2026 PS-P2 evaluation")
    print("=" * 64)
    print(f"records            : {n}")
    print(f"accuracy           : {res['accuracy']:.4f}")
    print(f"macro-F1 (headline): {res['macro_f1']:.4f}")
    print(f"UNKNOWN recall     : {res['unknown_recall']:.4f}")
    print(f"unsafe-unknown     : {unsafe_unknown}   (true UNKNOWN predicted as safe)")
    print(f"hash-as-public-key : {hash_as_pk}")
    print(f"missing / invalid  : {missing} / {invalid}    bad priority_score: {bad_scores}")
    if missing_cols:
        print(f"MISSING REQUIRED COLUMNS: {missing_cols}")
    print("\nper class               prec    rec     f1   support")
    for l in LABELS:
        v = per[l]
        print(f"  {l:20s} {v['precision']:6.3f} {v['recall']:6.3f} {v['f1']:6.3f} {v['support']:6d}")
    short = {"QUANTUM_VULNERABLE": "QV", "QUANTUM_RESISTANT": "QR", "HYBRID": "HY",
             "SYMMETRIC_OR_HASH": "SH", "LEGACY_BROKEN": "LB", "UNKNOWN": "UN", "MISSING/INVALID": "XX"}
    print("\nconfusion matrix (rows = true, cols = predicted)")
    hdr = list(cm[LABELS[0]].keys())
    print("      " + " ".join(f"{short[h]:>4s}" for h in hdr))
    for t in LABELS:
        print(f"  {short[t]:>3s} " + " ".join(f"{cm[t][p]:4d}" for p in hdr))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
        print(f"\nmetrics written to {a.json}")
    return 0 if not missing_cols else 2


if __name__ == "__main__":
    sys.exit(main())
