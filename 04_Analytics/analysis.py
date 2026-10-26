"""Runs queries.sql against the SYNTHETIC pipeline (SQLite in memory), saves result CSVs and charts.
Usage: python analysis.py  (expects the CSVs in ../03_CRM_Pipeline relative to this file)"""
import os, re, sqlite3, json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "03_CRM_Pipeline")
OUT = os.path.join(HERE, "outputs"); os.makedirs(OUT, exist_ok=True)

opp = pd.read_csv(os.path.join(DATA, "synthetic_opportunities.csv"))
snap = pd.read_csv(os.path.join(DATA, "weekly_pipeline_snapshots.csv"))
for c in ("Is_Closed", "Is_Won", "Primary_Deal"):
    opp[c] = opp[c].astype(int)
con = sqlite3.connect(":memory:")
opp.to_sql("opportunities", con, index=False)
snap.to_sql("snapshots", con, index=False)

sql = open(os.path.join(HERE, "queries.sql")).read()
blocks = re.split(r"^-- name: (\w+)\s*$", sql, flags=re.M)[1:]
results = {}
for name, body in zip(blocks[0::2], blocks[1::2]):
    df = pd.read_sql_query(body, con)
    results[name] = df
    df.to_csv(os.path.join(OUT, f"{name}.csv"), index=False)
    print(f"\n== {name}\n{df.to_string(index=False)}")

# ---------- charts (single-hue bars, direct labels, recessive axes)
S1, S2, INK, INK2, GRID, SURF = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF, "axes.facecolor": SURF})
overall = float(results["overall"].win_rate_count[0])


def hbar(df, cat, title, fname, note):
    d = df.sort_values("win_rate")
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ax.barh(d[cat], d.win_rate, color=S1, height=0.55)
    for y, (wr, n) in enumerate(zip(d.win_rate, d.closed_deals)):
        ax.text(wr + 0.01, y, f"{wr:.0%}  (n={n})", va="center", color=INK, fontsize=9, zorder=3,
                bbox=dict(facecolor=SURF, edgecolor="none", pad=1))
    ax.axvline(overall, color=INK2, lw=1, ls="--", zorder=1)
    ax.set_ylim(-0.95, len(d) - 0.5)
    ax.text(overall + 0.005, -0.8, f"overall {overall:.0%}", color=INK2, fontsize=8, va="center")
    ax.set_xlim(0, max(d.win_rate) + 0.2); ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.set_title(title, loc="left", color=INK, fontsize=12, fontweight="bold")
    fig.text(0.01, 0.01, note, fontsize=7.5, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(os.path.join(OUT, fname), dpi=160); plt.close(fig)


NOTE = "SYNTHETIC data, 150 fictional opportunities. Small n per group - directional only."
hbar(results["by_lead_source"], "Lead_Source", "Win rate by lead source", "chart_win_rate_lead_source.png", NOTE)
hbar(results["by_value_proposition"], "Value_Proposition", "Win rate by value proposition", "chart_win_rate_value_prop.png", NOTE)
hbar(results["by_segment"], "Segment", "Win rate by customer segment", "chart_win_rate_segment.png", NOTE)

lr = results["loss_reasons"].sort_values("lost_deals")
fig, ax = plt.subplots(figsize=(7.5, 3.6))
ax.barh(lr.Loss_Reason, lr.lost_deals, color=S2, height=0.55)
for y, (n, sh) in enumerate(zip(lr.lost_deals, lr.share)):
    ax.text(n + 0.3, y, f"{n}  ({sh:.0%})", va="center", color=INK, fontsize=9)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.set_xlim(0, lr.lost_deals.max() + 5)
ax.set_title("Why we lose: reasons on closed-lost deals", loc="left", color=INK, fontsize=12, fontweight="bold")
fig.text(0.01, 0.01, NOTE, fontsize=7.5, color=INK2)
fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(os.path.join(OUT, "chart_loss_reasons.png"), dpi=160); plt.close(fig)

w = results["weekly_q4_forecast"]
w["closed_plus_commit"] = w.closed_won_usd_m + w.commit_usd_m
fig, ax = plt.subplots(figsize=(8, 3.8))
x = pd.to_datetime(w.Snapshot_Date)
ax.plot(x, w.weighted_forecast_usd_m, color=S1, lw=2, marker="o", ms=4, label="Weighted forecast")
ax.plot(x, w.closed_plus_commit, color=S2, lw=2, marker="o", ms=4, label="Closed won + Commit")
for series, col in ((w.weighted_forecast_usd_m, S1), (w.closed_plus_commit, S2)):
    ax.annotate(f"${series.iloc[-1]:.0f}M", (x.iloc[-1], series.iloc[-1]), xytext=(6, 0), textcoords="offset points",
                color=INK, fontsize=9, va="center")
ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.set_ylabel("USD million"); ax.legend(frameon=False, loc="upper left")
ax.set_title("Q4-2026 bookings forecast - weekly snapshots", loc="left", color=INK, fontsize=12, fontweight="bold")
fig.text(0.01, 0.01, "SYNTHETIC data. Deals with close date Oct-Dec 2026. Weighted = amount x stage probability.", fontsize=7.5, color=INK2)
fig.autofmt_xdate(); fig.tight_layout(rect=(0, 0.04, 0.97, 1)); fig.savefig(os.path.join(OUT, "chart_weekly_forecast.png"), dpi=160); plt.close(fig)

json.dump({k: v.to_dict(orient="records") for k, v in results.items()}, open(os.path.join(OUT, "results.json"), "w"), indent=1)
print("\nCharts and CSVs written to", OUT)
