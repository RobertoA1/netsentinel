from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from app.services.reports.model import Chart  # noqa: E402

REPORT_DPI = 600  # todas las figuras de reportes se rasterizan a 600 DPI (7 x 3,2 in -> 4200 x 1920 px)
PALETTE = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed", "#0891b2", "#be185d"]


def png_size(png: bytes) -> tuple[int, int]:
    import struct

    return struct.unpack(">II", png[16:24])


def render_png(chart: Chart, width: float = 7.0, height: float = 3.2, dpi: int = REPORT_DPI) -> bytes:
    if chart.spec is not None:
        from app.ml.figures import render

        return render(chart.spec, "png", dpi, width)
    fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
    labels = [str(x)[:22] for x in chart.labels]
    try:
        if chart.kind == "pie":
            vals = next(iter(chart.series.values()), [])
            if sum(vals) <= 0:
                ax.text(0.5, 0.5, "Sin datos", ha="center", va="center")
                ax.axis("off")
            else:
                ax.pie(vals, labels=labels, autopct="%1.0f%%", colors=PALETTE, textprops={"fontsize": 7})
        elif chart.kind == "line":
            for i, (name, vals) in enumerate(chart.series.items()):
                ax.plot(range(len(vals)), vals, label=name, color=PALETTE[i % len(PALETTE)], marker="o", ms=3)
            step = max(1, len(labels) // 8)
            ax.set_xticks(range(0, len(labels), step))
            ax.set_xticklabels(labels[::step], rotation=30, ha="right", fontsize=7)
        elif chart.kind == "hbar":
            vals = next(iter(chart.series.values()), [])
            ax.barh(range(len(vals)), vals, color=PALETTE[0])
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels, fontsize=7)
            ax.invert_yaxis()
        else:
            n = max(1, len(chart.series))
            w = 0.8 / n
            for i, (name, vals) in enumerate(chart.series.items()):
                ax.bar([x + i * w for x in range(len(vals))], vals, w, label=name, color=PALETTE[i % len(PALETTE)])
            ax.set_xticks([x + 0.4 - w / 2 for x in range(len(labels))])
            ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=7)
        if chart.kind != "pie":
            ax.grid(axis="y" if chart.kind != "hbar" else "x", alpha=0.25)
            ax.spines[["top", "right"]].set_visible(False)
            ax.tick_params(labelsize=7)
            if chart.ylabel:
                (ax.set_xlabel if chart.kind == "hbar" else ax.set_ylabel)(chart.ylabel, fontsize=8)
            if len(chart.series) > 1:
                ax.legend(fontsize=7, frameon=False)
        ax.set_title(chart.title, fontsize=10, fontweight="bold")
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi)
        return buf.getvalue()
    finally:
        plt.close(fig)
