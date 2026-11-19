"""Renderizado de las especificaciones de figura (las mismas que dibuja el frontend) con matplotlib.
Reportes y exportación PNG/SVG: 600 DPI por defecto."""
from __future__ import annotations

import io
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, Normalize  # noqa: E402

REPORT_DPI = 600
PALETTE = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed", "#0891b2", "#be185d", "#64748b"]
SEQ = LinearSegmentedColormap.from_list("seq", ["#f8fafc", "#93c5fd", "#1d4ed8", "#1e1b4b"])
DIV = LinearSegmentedColormap.from_list("div", ["#b91c1c", "#fecaca", "#f8fafc", "#bfdbfe", "#1d4ed8"])
STATE_COLORS = {"complete": "#2563eb", "pruned": "#d97706", "fail": "#dc2626", "running": "#16a34a"}

SIZES = {"heatmap": (7.0, 4.2), "swarm": (7.0, 4.6), "parcoords": (7.0, 3.8), "waterfall": (7.0, 3.6)}


def _wrap(s: str, n: int = 24) -> str:
    return "\n".join(textwrap.wrap(str(s), n)) or str(s)


def _bars(ax, d):
    labels = [str(x) for x in d["labels"]]
    series = d["series"]
    n = max(1, len(series))
    hor = d.get("horizontal")
    pos = np.arange(len(labels))
    w = 0.8 / n
    for i, s in enumerate(series):
        vals = [np.nan if v is None else v for v in s["values"]]
        off = pos - 0.4 + w * (i + 0.5)
        err = s.get("err")
        col = s.get("color") or PALETTE[i % len(PALETTE)]
        if d.get("signed"):
            cols = [PALETTE[0] if (v or 0) >= 0 else PALETTE[1] for v in vals]
        else:
            cols = col
        if hor:
            ax.barh(off, vals, w, xerr=err, label=s["name"], color=cols, error_kw={"lw": 0.8})
        else:
            ax.bar(off, vals, w, yerr=err, label=s["name"], color=cols, error_kw={"lw": 0.8})
    if hor:
        ax.set_yticks(pos)
        ax.set_yticklabels([_wrap(x, 30) for x in labels], fontsize=6.5)
        ax.invert_yaxis()
        ax.set_xlabel(d.get("xlabel") or d.get("ylabel", ""), fontsize=7.5)
        if d.get("log"):
            ax.set_xscale("log")
        ax.grid(axis="x", alpha=0.25)
    else:
        ax.set_xticks(pos)
        ax.set_xticklabels([_wrap(x, 12) for x in labels], rotation=0 if len(labels) <= 6 else 35,
                           ha="center" if len(labels) <= 6 else "right", fontsize=6.5)
        ax.set_ylabel(d.get("ylabel", ""), fontsize=7.5)
        if d.get("xlabel"):
            ax.set_xlabel(d["xlabel"], fontsize=7.5)
        if d.get("log"):
            ax.set_yscale("log")
        ax.grid(axis="y", alpha=0.25)
    if n > 1:
        ax.legend(fontsize=6.5, frameon=False)


def _lines(ax, d):
    mode_all = d.get("mode")
    for i, s in enumerate(d["series"]):
        x, y = s["x"], s["y"]
        if s.get("state") or mode_all == "segments":
            ax.plot(x, y, color=STATE_COLORS.get(s.get("state", "complete"), PALETTE[0]), lw=3, solid_capstyle="butt")
            continue
        col = s.get("color") or PALETTE[i % len(PALETTE)]
        if s.get("mode") == "markers":
            ax.scatter(x, y, s=10, color=col, alpha=0.7, label=s["name"], linewidths=0)
        elif s.get("points"):
            sizes = s.get("sizes")
            sz = [20 + 80 * (n_ / max(sizes)) for n_ in sizes] if sizes else 20
            ax.plot(x, y, color=col, lw=1, alpha=0.8)
            ax.scatter(x, y, s=sz, color=col, label=s["name"], zorder=3)
        else:
            kw = dict(lw=2.2 if s.get("bold") else (0.6 if s.get("faint") else 1.4), alpha=0.35 if s.get("faint") else 1.0)
            ax.plot(x, y, color="#0f172a" if s.get("bold") else (col if not s.get("faint") else "#64748b"),
                    label=None if s.get("faint") else s["name"], **kw)
            if s.get("lo") is not None:
                ax.fill_between(x, s["lo"], s["hi"], color=col, alpha=0.18, linewidth=0)
    if d.get("diagonal"):
        ax.plot([0, 1], [0, 1], "--", color="#94a3b8", lw=1, label="Azar / ideal")
    for h in d.get("hlines", []):
        ax.axhline(h["y"], ls="--", color="#94a3b8", lw=1, label=h.get("label"))
    if d.get("xlim"):
        ax.set_xlim(d["xlim"])
    if d.get("ylim"):
        ax.set_ylim(d["ylim"])
    if d.get("xlog"):
        ax.set_xscale("log")
    if d.get("ylog"):
        ax.set_yscale("log")
    ax.set_xlabel(d.get("xlabel", ""), fontsize=7.5)
    ax.set_ylabel(d.get("ylabel", ""), fontsize=7.5)
    ax.grid(alpha=0.25)
    if d.get("legend", True) and ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=6.5, frameon=False)


def _dots(ax, d):
    for i, g in enumerate(d["groups"]):
        vals = [v for v in g["values"] if v is not None]
        x = np.full(len(vals), i) + np.linspace(-0.12, 0.12, max(len(vals), 1))[: len(vals)]
        ax.scatter(x, vals, s=22, color=PALETTE[i % len(PALETTE)], zorder=3)
        if vals:
            ax.hlines(np.mean(vals), i - 0.25, i + 0.25, color="#0f172a", lw=2)
    ax.set_xticks(range(len(d["groups"])))
    ax.set_xticklabels([_wrap(g["name"], 14) for g in d["groups"]], fontsize=7)
    ax.set_ylabel(d.get("ylabel", ""), fontsize=7.5)
    ax.grid(axis="y", alpha=0.25)


def _heatmap(fig, ax, d):
    vals = np.array([[np.nan if v is None else v for v in r] for r in d["values"]], dtype=float)
    cmap = DIV if d.get("scale") == "div" else SEQ
    vmin = d.get("vmin", np.nanmin(vals) if np.isfinite(vals).any() else 0)
    vmax = d.get("vmax", np.nanmax(vals) if np.isfinite(vals).any() else 1)
    if vmax == vmin:
        vmax = vmin + 1e-9
    im = ax.imshow(vals, aspect="auto", cmap=cmap, norm=Normalize(vmin, vmax))
    ax.set_xticks(range(len(d["cols"])))
    ax.set_xticklabels([_wrap(c, 10) for c in d["cols"]], rotation=45 if len(d["cols"]) > 6 else 0,
                       ha="right" if len(d["cols"]) > 6 else "center", fontsize=6)
    ax.set_yticks(range(len(d["rows"])))
    ax.set_yticklabels([_wrap(r, 28) for r in d["rows"]], fontsize=6.5)
    if d.get("xlabel"):
        ax.set_xlabel(d["xlabel"], fontsize=7.5)
    if d.get("ylabel"):
        ax.set_ylabel(d["ylabel"], fontsize=7.5)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label(d.get("vlabel", ""), fontsize=7)
    cb.ax.tick_params(labelsize=6)
    if d.get("annotate"):
        for i in range(vals.shape[0]):
            for j in range(vals.shape[1]):
                v = vals[i, j]
                if np.isnan(v):
                    continue
                txt = f"{int(v):,}" if d.get("fmt") == "int" else (f"{100 * v:.1f} %" if d.get("fmt") == "pct" else f"{v:.3f}")
                dark = (v - vmin) / (vmax - vmin) > 0.55
                ax.text(j, i, txt, ha="center", va="center", fontsize=8, color="white" if dark else "#0f172a")


def _swarm(ax, d):
    feats = d["features"]
    rng = np.random.default_rng(0)
    for i, f in enumerate(feats):
        x = np.array([p["x"] for p in f["points"]])
        c = np.array([p["c"] for p in f["points"]])
        ax.scatter(x, i + rng.uniform(-0.28, 0.28, len(x)), c=c, cmap="coolwarm", s=6, vmin=0, vmax=1, linewidths=0, alpha=0.8)
    ax.axvline(0, color="#94a3b8", lw=0.8)
    ax.set_yticks(range(len(feats)))
    ax.set_yticklabels([_wrap(f.get("label", f["feature"]), 28) for f in feats], fontsize=6.5)
    ax.invert_yaxis()
    ax.set_xlabel(d.get("xlabel", ""), fontsize=7.5)
    ax.grid(axis="x", alpha=0.25)


def _waterfall(ax, d):
    cur = d.get("base", 0.0)
    for i, it in enumerate(d["items"]):
        ax.barh(i, it["value"], left=cur, color=PALETTE[1] if it["value"] > 0 else PALETTE[0])
        cur += it["value"]
    ax.set_yticks(range(len(d["items"])))
    ax.set_yticklabels([_wrap(it["label"], 30) for it in d["items"]], fontsize=6.5)
    ax.invert_yaxis()
    ax.axvline(d.get("base", 0.0), color="#94a3b8", lw=0.8, ls="--")
    ax.set_xlabel(d.get("xlabel", "Contribución acumulada"), fontsize=7.5)


def _parcoords(ax, d):
    axes = d["axes"]
    k = len(axes)
    vals = np.array([l["value"] for l in d["lines"]])
    norm = Normalize(vals.min(), vals.max() if vals.max() > vals.min() else vals.min() + 1e-9)
    cmap = plt.get_cmap("viridis")

    def scale(a, v):
        if v is None:
            return 0.0
        if "categories" in a:
            cats = a["categories"]
            return cats.index(v) / max(len(cats) - 1, 1) if v in cats else 0.0
        lo, hi = a["min"], a["max"]
        if a.get("log") and lo > 0:
            lo, hi, v = np.log10(lo), np.log10(max(hi, lo * 1.0001)), np.log10(max(v, 1e-12))
        return (v - lo) / (hi - lo) if hi > lo else 0.5

    for l in sorted(d["lines"], key=lambda x: x["value"]):
        ax.plot(range(k), [scale(a, v) for a, v in zip(axes, l["values"])], color=cmap(norm(l["value"])), lw=1, alpha=0.7)
    for i in range(k):
        ax.axvline(i, color="#475569", lw=0.8)
    ax.set_xticks(range(k))
    ax.set_xticklabels([_wrap(a["name"], 12) for a in axes], fontsize=6.5)
    ax.set_yticks([])
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label(d.get("objective", ""), fontsize=7)
    cb.ax.tick_params(labelsize=6)


def render(spec: dict, fmt: str = "png", dpi: int = REPORT_DPI, width: float = 7.0) -> bytes:
    """spec: {kind, title, data}. Devuelve los bytes del PNG (con metadatos de DPI) o SVG."""
    kind, d = spec["kind"], spec.get("data", spec)
    w, h = SIZES.get(kind, (7.0, 3.4))
    if kind == "bars" and d.get("horizontal"):
        h = max(2.8, 0.26 * len(d["labels"]) + 1.2)
    if kind == "heatmap":
        h = max(2.2, min(5.0, 0.3 * len(d["rows"]) + 1.6))
    if kind == "swarm":
        h = max(3.0, 0.38 * len(d["features"]) + 1.0)
    fig, ax = plt.subplots(figsize=(width, h * width / w))
    try:
        if kind == "bars":
            _bars(ax, d)
        elif kind == "lines":
            _lines(ax, d)
        elif kind == "dots":
            _dots(ax, d)
        elif kind == "heatmap":
            _heatmap(fig, ax, d)
        elif kind == "swarm":
            _swarm(ax, d)
        elif kind == "waterfall":
            _waterfall(ax, d)
        elif kind == "parcoords":
            _parcoords(ax, d)
        else:
            ax.text(0.5, 0.5, f"Tipo de figura no soportado: {kind}", ha="center", va="center")
            ax.axis("off")
        ax.tick_params(labelsize=6.5)
        if kind not in ("heatmap",):
            ax.spines[["top", "right"]].set_visible(False)
        ax.set_title(_wrap(spec.get("title", ""), 90), fontsize=9, fontweight="bold")
        fig.tight_layout()
        buf = io.BytesIO()
        if fmt == "svg":
            fig.savefig(buf, format="svg")
        else:
            fig.savefig(buf, format="png", dpi=dpi)
        return buf.getvalue()
    finally:
        plt.close(fig)
