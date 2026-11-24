from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_revenue_by_month(metrics, out_dir):
    '''Выручка по месяцам.'''
    data = metrics.sort_values("month")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(data["month"], data["revenue"] / 1_000_000, color="#4C72B0")
    ax.set_title("Выручка по месяцам")
    ax.set_xlabel("Месяц")
    ax.set_ylabel("Выручка, млн руб.")
    ax.set_ylim(0, (data["revenue"].max() / 1_000_000) * 1.2)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()

    path = Path(out_dir) / "revenue_by_month.png"
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_plan_vs_fact(plan_fact, out_dir, target=100):
    '''Выполнение плана по выручке в разрезе маршрутов.'''
    data = plan_fact.sort_values("revenue_done_pct")
    colors = ["#55A868" if v >= target else "#C44E52" for v in data["revenue_done_pct"]]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(data["route"], data["revenue_done_pct"], color=colors)
    ax.axvline(target, color="black", linestyle="--", linewidth=1.5,
               label=f"план: {target}%")
    ax.set_title("Выполнение плана по выручке")
    ax.set_xlabel("Факт к плану, %")
    ax.set_xlim(0, max(110, data["revenue_done_pct"].max() * 1.1))
    ax.legend()
    fig.tight_layout()

    path = Path(out_dir) / "plan_vs_fact.png"
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path
