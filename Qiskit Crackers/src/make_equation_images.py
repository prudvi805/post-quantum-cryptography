from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = Path("assets") / "qff_phase1_latex_images"

EQUATIONS = {
    "eq_qubit_state": r"$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle,\quad |\alpha|^2 + |\beta|^2 = 1$",
    "eq_bell_state": r"$|\Phi^{+}\rangle = \frac{1}{\sqrt{2}}\left(|00\rangle + |11\rangle\right)$",
    "eq_graph": r"$|G\rangle = \prod_{(i,j)\in E} CZ_{ij}\,|+\rangle^{\otimes n}$",
    "eq_bell_fidelity": r"$F = \langle\Phi^{+}|\rho|\Phi^{+}\rangle$",
    "eq_zz_expectation": r"$\langle Z_0 Z_1\rangle = \frac{N_{00} + N_{11} - N_{01} - N_{10}}{N}$",
    "eq_standard_error": r"$\sigma_{\hat{p}} = \sqrt{\frac{\hat{p}\,(1-\hat{p})}{N}}$",
}

OUT_DIR.mkdir(parents=True, exist_ok=True)
for name, tex in EQUATIONS.items():
    fig = plt.figure(figsize=(6, 1.2))
    fig.text(0.5, 0.5, tex, ha="center", va="center", fontsize=20)
    fig.savefig(OUT_DIR / f"{name}.png", dpi=200, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("Created:", name + ".png")
print("All six PNG images created successfully.")