# Postmortem

## What worked
- The scanner runs on the labelled corpus and reports precision, recall, F1 and timing.
- Migration mapping to FIPS 203 and 204 is generated for each finding.
- The report, tables and figures regenerate from one command.
- Scanner-only mode runs without Qiskit or network access.

## What did not work well
- **The quantum benchmark was not run end-to-end before handover.** The code was written against the Qiskit 1.x API and reviewed by reading, but a real run may expose errors. The pinned versions in `requirements.txt` were also not checked against an installed environment.
- **Setup was harder than expected on Windows.** Missing packages, interpreter selection, and terminal output confusion each took several rounds to diagnose. Clearer step-by-step instructions at the start would have helped.
- **Output folders looked empty.** Placeholder files and the scanner-only mode meant some folders stayed empty, which was confusing. The README should have explained this earlier.
- **The problem statement and the Phase 1 specification do not match.** A classical scanner was combined with a quantum benchmark. This needs confirmation from the organisers.

## Limitations accepted
- Scanner covers Python only and misses calls through wrapper libraries.
- Labelled corpus is small and written by the same team, so its precision and recall are optimistic.
- Public repo precision depends on manual review that has not yet been done.

## Next time
- Run the full pipeline end-to-end in the first hour, not the last.
- Check the problem statement against the rubric before building.
- Keep a running log of questions and answers, so the prompts file is easy to complete.
