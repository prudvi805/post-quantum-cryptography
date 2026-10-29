# Issues Log

| # | Issue | Cause | Resolution |
|---|---|---|---|
| 1 | `ModuleNotFoundError: networkx` when running `python -m src.pipeline` | Dependencies in `requirements.txt` were not installed on the machine | Ran `python -m pip install -r requirements.txt` |
| 2 | Could not select a Python interpreter in VS Code (Ctrl+Shift+P) | VS Code command palette wording and Python extension state differed | Not needed: the terminal uses the Python that pip installed into. Used `python -m ...` commands directly |
| 3 | Terminal showed no output after running a command | Command was not entered or the prompt had not returned | Confirmed the folder with `dir`, then ran the command again |
| 4 | `assets/qff_phase1_latex_images/` appeared empty | Folder only contains `.gitkeep`, a placeholder. Equation PNGs were never created | Folder is optional. Equation images must be exported separately |
| 5 | Ctrl+Shift+V did not show a preview of `report.md` | The preview needs the report open in the editor | Opened the Preview tab alongside the raw file |
| 6 | `data/processed/` empty | Only public-repo runs write there, and those were skipped with `--skip-repos` | Requires a full run with network and Git. Review CSVs are written there |
| 7 | Quantum benchmark not yet run end-to-end | Qiskit was not installed in the development sandbox, which also had no network | **Open.** Must run `python -m src.pipeline --skip-repos` on the target machine and check the output |
| 8 | Public repository precision is pending | Repos are unlabelled; a person must review findings | **Open.** Fill `is_true_positive` in the review CSVs and rerun |
| 9 | Known scanner miss: calls through wrapper libraries | AST scanner resolves only direct imports | Documented as a limitation. Labelled in the corpus so recall is honest |
| 10 | Import error for `networkx` in the first full run and an `ImportError` on some runs | Libraries not yet installed in the active Python | Resolved by installing requirements into the same Python used to run the code |
