"""Plots for the benchmark and the scanner. Each function saves a PNG and returns the path."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402

PALETTE = {"A": "#2F6FDE", "B": "#2E9E5B"}


def save(fig, path):
    path = Path(path)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def plot_coupling_map(cfg, path, color):
    graph = nx.Graph()
    graph.add_nodes_from(range(cfg["num_qubits"]))
    graph.add_edges_from(tuple(e) for e in cfg["coupling_map"])
    pos = nx.spring_layout(graph, seed=42)

    fig, ax = plt.subplots(figsize=(5, 4))
    nx.draw_networkx(graph, pos=pos, ax=ax, node_color=color, font_color="white",
                     node_size=700, width=2)
    ax.set_title(f"{cfg['name']}: {cfg['num_qubits']} qubits, {len(cfg['coupling_map'])} edges")
    ax.axis("off")
    return save(fig, path)


def plot_scaling(df, path):
    panels = [
        ("depth_routed", "Routed circuit depth"),
        ("cx_routed", "CX count after routing"),
        ("p_success_noisy", "GHZ success probability (noisy)"),
    ]
    sizes = sorted(df["logical_qubits"].unique())

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, (col, title) in zip(axes, panels):
        for proc, group in df.groupby("processor"):
            ax.plot(group["logical_qubits"], group[col], marker="o",
                    color=PALETTE[proc], label=f"Processor {proc}")
        ax.set_title(title)
        ax.set_xlabel("Logical qubits (GHZ size)")
        ax.set_xticks(sizes)
        ax.grid(alpha=0.3)
    axes[0].legend()
    return save(fig, path)


def grouped_bars(ax, head, cols, names, title, ylabel, ylim=None):
    """Side-by-side bars, one cluster per processor."""
    labels = [f"Processor {p}" for p in head["processor"]]
    x = list(range(len(head)))
    width = 0.8 / len(cols)

    for i, (col, name) in enumerate(zip(cols, names)):
        ax.bar([xi + i * width for xi in x], head[col], width=width, label=name)

    ax.set_xticks([xi + width * (len(cols) - 1) / 2 for xi in x])
    ax.set_xticklabels(labels)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    ax.legend(fontsize=8)


def plot_headline(head, path):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    grouped_bars(axes[0], head, ["depth_all_to_all", "depth_routed"], ["all-to-all", "routed"],
                 "Circuit depth (5 logical qubits)", "depth")
    grouped_bars(axes[1], head, ["cx_all_to_all", "cx_routed"], ["all-to-all", "routed"],
                 "CX count (5 logical qubits)", "CX gates")
    grouped_bars(axes[2], head, ["p_success_ideal", "p_success_noisy"], ["ideal", "noisy"],
                 "GHZ success probability", "probability", ylim=(0, 1.05))
    return save(fig, path)


def plot_scanner(per_family, findings_df, path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    if not per_family.empty:
        x = list(range(len(per_family)))
        width = 0.27
        series = [("precision", "#2F6FDE"), ("recall", "#2E9E5B"), ("f1", "#E0A100")]
        for i, (col, color) in enumerate(series):
            ax1.bar([xi + i * width for xi in x], per_family[col], width=width,
                    label=col, color=color)
        ax1.set_xticks([xi + width for xi in x])
        ax1.set_xticklabels(per_family["family"])
        ax1.set_ylim(0, 1.05)
        ax1.set_title("Scanner precision / recall / F1 by family")
        ax1.legend()

    if not findings_df.empty:
        counts = findings_df.groupby(["family", "usage"]).size().unstack(fill_value=0)
        counts.plot(kind="bar", stacked=True, ax=ax2, rot=0)
        ax2.set_title("Findings by family and migration usage")
        ax2.set_ylabel("findings")

    return save(fig, path)


def plot_repo_timing(ok_df, path):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(ok_df["lines"], ok_df["scan_time_s"], color="#2F6FDE")
    for _, row in ok_df.iterrows():
        ax.annotate(row["repo"], (row["lines"], row["scan_time_s"]),
                    xytext=(5, 5), textcoords="offset points")
    ax.set_xlabel("Lines of Python scanned")
    ax.set_ylabel("Scan time (s)")
    ax.set_title("Scanner runtime on public repositories")
    ax.grid(alpha=0.3)
    return save(fig, path)
