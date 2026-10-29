# Patterns Used

**Import-aware call matching.** Build an alias map from `import` statements, then resolve each call's root name through it before matching. Unresolved names are ignored. Used in `src/scanner.py`.

**Deduplicate per line.** One source line can contain several calls in the same family, such as `ec.generate_private_key(ec.SECP256R1())`. Keep one finding per (line, family), the highest severity. Used in `scan_source`.

**Keep severity and usage separate.** Severity comes from the operation name (generation is HIGH). Usage comes from the library and nearby text. Both are reported so that the migration target can be chosen.

**Ground truth as inline markers.** Lines that should be flagged carry `# EXPECT: <FAMILY>`. The evaluator reads the markers, so the expected answers sit next to the code. Used in `src/evaluate.py`.

**Canary recall for unlabelled repos.** Copy labelled positive snippets into a temporary copy of the repo, then check they are found. This gives a measured recall without labels.

**Human review sheet, never overwritten.** The pipeline writes review CSVs only if they don't exist, so a reviewer's labels are never lost on rerun.

**Pinned configuration in JSON.** Processor definitions, noise and transpile settings live in `processors/*.json`. Code reads them, so the two processors differ only in their data.

**Lazy heavy imports.** Qiskit, matplotlib and networkx are imported inside the functions that need them. The scanner runs with `--skip-quantum` without them.

**Generated report.** `report.md` is rebuilt on every run from the tables, so numbers in it always match the code.
